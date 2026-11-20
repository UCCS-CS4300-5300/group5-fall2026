from django import forms
from .models import GlobalCatalogItem, PantryItem


class PantryItemForm(forms.ModelForm):

    # A <select> of 661 USDA foods is unusable -- the user scrolls past
    # "Amaranth (flour, meal)" looking for milk. A text input backed by a
    # <datalist> lets the browser filter as they type, with no JavaScript
    # and no extra request. The list itself lives in home.html so it is
    # rendered once per page rather than once per edit pop-up.
    #
    # Declaring it as a CharField overrides the ModelForm's ModelChoiceField.
    # clean_catalog_item hands back a real GlobalCatalogItem when the typed
    # name matches one, and None when it does not -- a custom food. The
    # typed text is kept and saved to custom_name instead.
    catalog_item = forms.CharField(
        label="Food",
        help_text="Pick one from the list, or type your own.",
        widget=forms.TextInput(attrs={
            "list": "catalog-options",
            "autocomplete": "off",
            "class": "form-control",
            "placeholder": "Start typing, or name your own food",
        }),
    )

    class Meta:
        model = PantryItem

        # TODO add pantry names for the visible pantry
        fields = ["catalog_item", "quantity","date_stored","date_expired", "location"]

        widgets = {
            "quantity": forms.NumberInput(attrs={"min": 1, "class":"form-control"}),
            "date_stored": forms.DateInput(attrs={"type": "date", "class":"form-control"}),
            "date_expired": forms.DateInput(attrs={"type":"date","class":"form-control"}),
            "location": forms.Select(attrs={"class":"form-control"})
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.fields["date_expired"].required = False

        # A custom food has no USDA shelf life to compute from, so the user
        # is the only source of an expiry date. Leaving it blank is allowed
        # and shows as "Unknown", same as the 14 catalog foods the USDA
        # gives no figure for anywhere.
        self.fields["date_expired"].help_text = (
            "Optional. Left blank, we work it out from USDA data where we "
            "can.")

        # ModelForm fills initial from the instance, which for a foreign key
        # is the id -- the edit pop-up would open showing "41". Show the
        # same text the datalist offers instead, or the custom name.
        if self.instance.pk:
            if self.instance.catalog_item_id:
                self.initial["catalog_item"] = str(self.instance.catalog_item)
            elif self.instance.custom_name:
                self.initial["catalog_item"] = self.instance.custom_name

    def clean_catalog_item(self):
        """Turn what the user typed into a catalog row, or None.

        The datalist offers each food as str(item) -- "Beef (ground)" -- so
        match on that whole string rather than parsing it apart. Guessing
        where a name ends and a subtitle begins goes wrong on entries like
        '"Genuine" Maple syrup (unopened, glass)'.

        A name that matches nothing is not an error any more: it is a food
        the USDA has not heard of, which people eat plenty of. It comes
        back as None and save() stores the text in custom_name.
        """
        typed = (self.cleaned_data.get("catalog_item") or "").strip()
        if not typed:
            raise forms.ValidationError("Give the food a name.")

        # One query, 661 comparisons. Cheap enough, and exact.
        for item in GlobalCatalogItem.objects.all():
            if str(item).casefold() == typed.casefold():
                return item

        # Someone who types "Cereal" and means it shouldn't have to add the
        # parenthetical, as long as only one food answers to that name.
        by_name = list(GlobalCatalogItem.objects.filter(name__iexact=typed))
        if len(by_name) == 1:
            return by_name[0]

        # Several catalog foods share this name, so we genuinely cannot
        # tell which was meant. Still an error -- treating it as a custom
        # food would quietly throw away the USDA shelf life they were
        # entitled to.
        if by_name:
            raise forms.ValidationError(
                f"There are {len(by_name)} foods called “{typed}”. "
                "Pick the specific one from the list.")

        # Nothing in the catalog answers to it. Custom food.
        self._custom_name = typed
        return None

    def save(self, commit=True):
        """Carry the typed name through when there is no catalog row.

        construct_instance assigns cleaned_data["catalog_item"], which is
        None for a custom food, so custom_name has to be set here or the
        item saves with no name at all.
        """
        item = super().save(commit=False)

        if item.catalog_item is None:
            item.custom_name = getattr(self, "_custom_name", "")
        else:
            item.custom_name = ""

        if commit:
            item.save()

        return item