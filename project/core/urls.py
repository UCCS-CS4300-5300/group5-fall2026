from django.urls import path
from . import views

app_name="core"

urlpatterns=[
    path("",views.home,name="home"),
    path('add_pantry_item/', views.add_pantry_item, name='add_pantry_item'),
    path('delete_pantry_item/<int:id>/', views.delete_pantry_item, name='delete_pantry_item'),
    path('edit_pantry_item/<int:id>/', views.edit_pantry_item, name='edit_pantry_item'),
    path('test-pantry/', views.test_pantry_view, name="test_pantry"),

    # Show the details for one pantry item.
    path(
        'items/<int:item_id>/',
        views.pantry_item_detail,
        name='pantry_item_detail'
    ),
    path('submit-drag-drop/', views.submit_drag_drop, name='submit_drag_drop'),
]
