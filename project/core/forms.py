from django import forms
from .models import PantryItem

class PantryItemForm(forms.ModelForm):
    # name = forms.CharField(max_length=100, label="Your Name")
    class Meta:    
        model = PantryItem
        fields = ["catalog_item", "quantity", "date_stored", "date_expired"]
        widgets = {
            "date_stored": forms.DateInput(attrs = {"type": "date"}),
            "date_expired": forms.DateInput(attrs = {"type": "date"}),
        }

# # Standard Form Example
# class ContactForm(forms.Form):
#     name = forms.CharField(max_length=100, label="Your Name")
#     email = forms.EmailField(label="Your Email")
#     message = forms.CharField(widget=forms.Textarea, label="Message")

# # ModelForm Example (Maps to an existing Article model)
# class ArticleForm(forms.ModelForm):
#     class Meta:
#         model = Article
#         fields = ['title', 'content', 'published_date']
