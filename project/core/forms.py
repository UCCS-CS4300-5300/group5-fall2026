from django import forms
from .models import GlobalCatalogItem, PantryItem


class PantryItemForm(forms.ModelForm):

    # A <select> of 661 USDA foods is unusable -- the user scrolls past
    # "Amaranth (flour, meal)" looking for milk. A text input backed by a
    # <datalist> lets the browser filter as they type, with no JavaScript
    # and no extra request. The list itself lives in home.html so it is
    # rendered once per page rather than once per edit pop-up.
    #
    # Declaring it as a CharField overrides the ModelForm's ModelChoiceField,
    # so clean_catalog_item has to hand back a real GlobalCatalogItem for
    # form.save() to assign.
    catalog_item = forms.CharField(
        label="Catalog Item",
        widget=forms.TextInput(attrs={
            "list": "catalog-options",
            "autocomplete": "off",
            "class": "form-control",
            "placeholder": "Start typing: milk, beef, cereal...",
        }),
    )

    class Meta:
        model = PantryItem

        # TODO add pantry names for the visible pantry
        # TODO add ability for an item not in the catalog.
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

        # ModelForm fills initial from the instance, which for a foreign key
        # is the id -- the edit pop-up would open showing "41". Show the same
        # text the datalist offers instead.
        if self.instance.pk and self.instance.catalog_item_id:
            self.initial["catalog_item"] = str(self.instance.catalog_item)

    def clean_catalog_item(self):
        """Turn what the user typed back into a catalog row.

        The datalist offers each food as str(item) -- "Beef (ground)" -- so
        match on that whole string rather than parsing it apart. Guessing
        where a name ends and a subtitle begins goes wrong on entries like
        '"Genuine" Maple syrup (unopened, glass)'.
        """
        typed = (self.cleaned_data.get("catalog_item") or "").strip()
        if not typed:
            raise forms.ValidationError("Pick a food from the list.")

        # One query, 661 comparisons. Cheap enough, and exact.
        for item in GlobalCatalogItem.objects.all():
            if str(item).casefold() == typed.casefold():
                return item

        # Someone who types "Cereal" and means it shouldn't have to add the
        # parenthetical, as long as only one food answers to that name.
        by_name = list(GlobalCatalogItem.objects.filter(name__iexact=typed))
        if len(by_name) == 1:
            return by_name[0]

        if by_name:
            raise forms.ValidationError(
                f"There are {len(by_name)} foods called “{typed}”. "
                "Pick the specific one from the list.")

        raise forms.ValidationError(
            f"No catalog food called “{typed}”. Start typing and "
            "choose one from the list, or use the search box above.")