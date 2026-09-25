from django.shortcuts import render, redirect, get_object_or_404
#can be used when we start requiring logins into webpage
#from django.contrib.auth.decorators import login_required
from .models import PantryItem, Pantry
from .forms import PantryItemForm

"""Original Prof code
from .models import StarterItem
def home(request): return render(request,"core/home.html",{"items":StarterItem.objects.filter(is_active=True).order_by("title")})
"""

def home(request):
    #used to query item models and display in homepage
    items.PantryItem.objects.all()
    return render(request, "core/home.html", {"items":items})

def add_pantry_item(request):
    #first existing pantry for now
    pantry = Pantry.objects.first()

    if request.method == "POST":
        form = PantryItemForm(request.POST)
        if form.is_valid():
            #pantry isn't set yet
            item = form.save(commit=False)
            #attach item to pantry
            item.pantry = pantry
            item.save()
            return redirect("home")
    else:
        #empty form for GET request
        form = PantryItemForm()

    return render(request, "core/add_item.html", {"form":form})

def delete_pantry_item(request, item_id):
    #any item can be deleted by id
    item = get_onject_or_404(PantryItem, id=item_id)

    if request.method == "POST":
        item.delete()
        return redirect("home")

    return render(request, "core/delete_item.html", {"item": item})
