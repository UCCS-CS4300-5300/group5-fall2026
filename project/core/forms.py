from django import forms
from .models import PantryItem

class PantryItemForm(forms.ModelForm):
    # name = forms.CharField(max_length=100, label="Your Name")
    class Meta:    
        model = PantryItem
        # TODO add pantry names for the visible pantry
        # TODO add ability for an item not in the catalog.
        fields = ["catalog_item", "quantity", "date_stored", "date_expired"]
        widgets = {
            "date_stored": forms.DateInput(attrs = {"type": "date"}),
            "date_expired": forms.DateInput(attrs = {"type": "date"}),
        }
