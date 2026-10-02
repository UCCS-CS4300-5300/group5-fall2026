from django.urls import path
from . import views

app_name="core"

urlpatterns=[
    path("",views.home,name="home"),
    path(
        "items/<int:item_id>/",
        views.pantry_item_detail,
        name="pantry_item_detail"
    ),
]