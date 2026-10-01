from django import forms
from .models import PantryItem

class PantryItemForm(forms.ModelForm):
    class Meta:
        model = PantryItem
        fields = ["catalog_item", "quantity", "date_stored", "date_expired"]
        widgets = {
            "date_stored": forms.DateInput(attrs = {"type": "date"}),
            "date_expired": forms.DateInput(attrs = {"type": "date"}),
        }
