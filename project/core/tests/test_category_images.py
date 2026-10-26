import csv
from pathlib import Path

from core.templatetags.custom_elements import (
    FOOD_CATEGORY_IMAGES,
    food_category_image,
)


CATEGORIES_FIXTURE = (
    Path(__file__).resolve().parent.parent / "fixtures" / "foodkeeper_categories.csv"
)
IMAGE_DIRECTORY = (
    Path(__file__).resolve().parent.parent / "static" / "images" / "food-categories-images"
)


def catalog_categories():
    categories = set()
    with CATEGORIES_FIXTURE.open(newline="", encoding="utf-8") as fixture:
        for row in csv.DictReader(fixture):
            category = row["name"]
            if row["subcategory"]:
                category += ": " + row["subcategory"]
            categories.add(category)
    return categories


def test_all_catalog_categories_have_image_mapping():
    categories = catalog_categories()

    assert len(categories) == 25
    assert set(FOOD_CATEGORY_IMAGES) == categories

    for category in categories:
        image_name = food_category_image(category)
        assert image_name == FOOD_CATEGORY_IMAGES[category]
        assert (IMAGE_DIRECTORY / image_name).is_file()


def test_non_catalog_category_uses_unknown_image():
    assert food_category_image("Fruit") == "unknown-food.png"
    assert food_category_image("Dairy") == "unknown-food.png"
    assert food_category_image("User-created category") == "unknown-food.png"
    assert food_category_image(None) == "unknown-food.png"
