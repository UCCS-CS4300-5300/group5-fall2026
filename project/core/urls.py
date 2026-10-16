from django.urls import path
from . import views
 
app_name="core"
 
urlpatterns=[
    path("",views.home,name="home"),
    path('add_pantry_item/', views.add_pantry_item, name='add_pantry_item'),
    path('delete_pantry_item/<int:id>/', views.delete_pantry_item, name='delete_pantry_item'),
    path('edit_pantry_item/<int:id>/', views.edit_pantry_item, name='edit_pantry_item'),
 
    # Add one catalog food to the pantry in a single click, from a search result.
    path('add_from_catalog/<int:item_id>/', views.add_from_catalog, name='add_from_catalog'),
 
    # Show the details for one pantry item.
    path(
        'items/<int:item_id>/',
        views.pantry_item_detail,
        name='pantry_item_detail'
    ),
]
