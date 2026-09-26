from django.contrib import admin
from .models import GlobalCatalogItem,Pantry,PantryItem
#admin.site.register(StarterItem)

# For migrations
admin.site.register(GlobalCatalogItem)
admin.site.register(Pantry)
admin.site.register(PantryItem)