from django.shortcuts import render
from .models import PantryItem

def home(request):
    # This will be used to query item modles and display them in the homepage
    items = PantryItem.objects.all()
    return render(request, "core/home.html", {"items":items})

# Original starter item
"""from .models import StarterItem
def home(request): return render(request,"core/home.html",{"items":StarterItem.objects.filter(is_active=True).order_by("title")})"""