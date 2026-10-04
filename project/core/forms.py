from django import forms
from .models import PantryItem

class PantryItemForm(forms.ModelForm):

    class Meta:    
        model = PantryItem

        # TODO add pantry names for the visible pantry
        # TODO add ability for an item not in the catalog.
        fields = ["catalog_item", "quantity","date_stored","date_expired"]

        widgets = {
            "quantity": forms.NumberInput(attrs={"min": 1, "class":"form-control"}),
            "date_stored": forms.DateInput(attrs={"type": "date", "class":"form-control"}),
            "date_expired": forms.DateInput(attrs={"type":"date","class":"form-control"})
        }

def __init__(self, *args, **kwargs):
    """
    This function will flag date fields as non-required at the form tier.
    This will allow the calculation to be automatic and execute safely.
    """
    super().__init__(*args, **kwargs)
    self.fields["date_expired"].required = False

    