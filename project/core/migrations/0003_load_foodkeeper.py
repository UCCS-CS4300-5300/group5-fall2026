"""Load the USDA FoodKeeper catalog.

Source: FSIS FoodKeeper data, USDA Food Safety and Inspection Service.
Public domain (CC0). https://catalog.data.gov/dataset/fsis-foodkeeper-data

Loads 661 foods across 25 categories, with 1347 shelf-life rows.

Safe to run more than once: rows are matched on name + subtitle + category.
"""

import csv
from pathlib import Path

from django.db import migrations

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def number(value):
    """FoodKeeper leaves some numeric cells blank or with stray text."""
    return int(value) if value else None


def load(apps, schema_editor):
    CatalogItem = apps.get_model("core", "GlobalCatalogItem")
    ShelfLife = apps.get_model("core", "ShelfLife")

    # category id -> "Meat: Fresh"
    categories = {}
    with (FIXTURES / "foodkeeper_categories.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            label = row["name"]
            if row["subcategory"]:
                label = f"{label}: {row['subcategory']}"
            categories[row["id"]] = label

    items = {}
    with (FIXTURES / "foodkeeper_products.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            item, _ = CatalogItem.objects.get_or_create(
                name=row["name"],
                name_subtitle=row["name_subtitle"],
                category=categories[row["category_id"]],
                defaults={"keywords": row["keywords"]},
            )
            items[row["id"]] = item

    with (FIXTURES / "foodkeeper_shelf_life.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            ShelfLife.objects.update_or_create(
                item=items[row["product_id"]],
                storage=row["storage"],
                condition=row["condition"],
                defaults={
                    "min_amount": number(row["min_amount"]),
                    "max_amount": number(row["max_amount"]),
                    "metric": row["metric"],
                    "days_max": number(row["days_max"]),
                    "tips": row["tips"],
                },
            )


def unload(apps, schema_editor):
    apps.get_model("core", "ShelfLife").objects.all().delete()
    apps.get_model("core", "GlobalCatalogItem").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_globalcatalogitem_options_and_more"),  # set to your makemigrations output
    ]

    operations = [
        migrations.RunPython(load, unload),
    ]
