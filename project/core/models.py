import logging
from django.db import models
from django.contrib.auth.models import User # Django built-in user model
from django.utils import timezone # Useful for date tracking
from datetime import timedelta
from django.conf import settings 
 
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(module)s (Line %(lineno)d): %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("app.log", mode='w'),  # overwrites the file
        logging.StreamHandler()                    # Outputs to console
    ]
)
 
 
# Shared list of global item catalog
class GlobalCatalogItem(models.Model):
   """ 
   This is the shared list of all the items, loaded from USDA FoodKeeper.
   Below are going to be the fields of the items
   """
 
   # NOT unique. FoodKeeper lists 20 kinds of Ham, 12 of Pork, 5 of Cheese.
   # 193 of the 661 foods share a name with another entry, so unique=True
   # would make the catalog impossible to load.
   name = models.CharField(max_length=100)
 
   # What tells the variants apart, e.g. "hard such as cheddar, swiss"
   name_subtitle = models.CharField(max_length=200, blank=True)
 
   # Comma-separated search terms from FoodKeeper, so "stew meat" finds the
   # right entry. This is what makes catalog search usable.
   keywords = models.TextField(blank=True)
 
   # Still text, e.g. "Meat: Fresh". Longest value in the data is 33 chars.
   category = models.CharField(max_length=50)
 
   class Meta:
      # Category is part of the key: "Raw kabobs with vegetables" is listed
      # under both Meat and Poultry, with different shelf lives.
      unique_together = [("name", "name_subtitle", "category")]
      ordering = ["name"]
 
   def __str__(self):
      if self.name_subtitle:
         return f"{self.name} ({self.name_subtitle})"
      return self.name
 
   def shelf_life_days(self, storage=None, condition="purchase"):
      """
      How many days this food keeps in `storage`, or None when the USDA
      gives no figure for it.
 
      With no storage given, returns the best figure available, preferring
      fridge then pantry then freezer. That matters before the Storage
      Locations story exists: cereal has no refrigerator figure at all, so
      defaulting to the fridge would leave every shelf-stable food with no
      expiration date.
 
      With a storage given, stays within that location. Falls back from the
      requested condition to from-purchase, then to any condition, because
      FoodKeeper does not fill in every combination.
      """
      rows = self.shelf_lives.exclude(days_max=None)
 
      places = [storage] if storage else ["refrigerate", "pantry", "freeze"]
      for place in places:
         here = rows.filter(storage=place)
         match = here.filter(condition=condition).first() or here.first()
         if match:
            return match.days_max
 
      return None
 
 
class ShelfLife(models.Model):
   """
   How long one food keeps in one place, under one condition.
 
   Chicken is 2 days in the fridge and 360 days in the freezer, so a single
   number per food cannot express the real data.
   """
 
   STORAGE = [
      ("pantry", "Pantry"),
      ("refrigerate", "Fridge"),
      ("freeze", "Freezer"),
   ]
   CONDITION = [
      ("unopened", "Unopened"),
      ("purchase", "From purchase"),
      ("opened", "After opening"),
      ("thawed", "After thawing"),
   ]
 
   item = models.ForeignKey(GlobalCatalogItem, on_delete=models.CASCADE,
                            related_name="shelf_lives")
   storage = models.CharField(max_length=20, choices=STORAGE)
   condition = models.CharField(max_length=20, choices=CONDITION)
 
   min_amount = models.PositiveSmallIntegerField(null=True, blank=True)
   max_amount = models.PositiveSmallIntegerField(null=True, blank=True)
 
   # FoodKeeper's own wording: Days, Weeks, Months, Years, but also
   # "Indefinitely", "When Ripe", "Not Recommended", "Package use-by date".
   metric = models.CharField(max_length=40, blank=True)
 
   # max_amount converted to days. None when metric is not a time span,
   # which is 127 of the 1347 rows.
   days_max = models.PositiveIntegerField(null=True, blank=True)
 
   tips = models.TextField(blank=True)
 
   class Meta:
      unique_together = [("item", "storage", "condition")]
 
   def __str__(self):
      return f"{self.item.name} {self.get_storage_display()}: {self.metric}"
 
 
class Pantry(models.Model):
   """
    This will be the main pantry model for the user.
   """
 
   # OneToOnefield makes sure the user can only have one pantry
   user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="pantry")
   name = models.CharField(max_length=100, default="Main Pantry")
   created_at = models.DateTimeField(default=timezone.now) # keeping track of when it was created
 
   def __str__(self):
      return f"{self.user.username}'s {self.name}"
 
class PantryItem(models.Model):
   """
   This will keep track of the item inside the user's pantry
   """
 
   # foreign key is used for indicating which model it belongs to and
   # on the following field it makes sure there are can be duplicates
   pantry = models.ForeignKey(Pantry, on_delete=models.CASCADE, related_name="items")
   catalog_item = models.ForeignKey(GlobalCatalogItem, on_delete=models.CASCADE)
   quantity = models.PositiveSmallIntegerField(default=1)
 
   date_stored = models.DateField(default=timezone.localdate)
   date_expired = models.DateField(blank=True, null=True) # fields inside make it posible to accept empty inputs
 
   # TODO: Do we want to use a color border around the circle/image food item for drawing the user's Eye to the fact that the food is expiring?  
 
   @property
   def expiration_status(self): 
      """
      This function will help calculate the status of the expiration
      """
 
      if not self.date_expired:
         return "Unknown"
 
      today = timezone.localdate() # made it localdate for more accurate date representation
      
      logging.debug("________")
 
      logging.debug("(self.date_expired - today).days: \t" + str((self.date_expired - today).days))
      logging.debug("settings.EXPIRING_SOON_DAYS: \t" + str(settings.EXPIRING_SOON_DAYS))
 
      if today >= self.date_expired: #Fixed
         return "Expired"
      
      elif 0 < (self.date_expired - today).days <= settings.EXPIRING_SOON_DAYS:
         return "Expiring Soon"
 
      # Otherwise it is categorized as fresh for simplicity
      return "Fresh"
   
 
   def save(self, *args, **kwargs):
      """
      This will make it possible to automatically compute expiration dates
      based on USDA shelf-life data if the fields are left empty.
      """
 
      if not self.date_expired and self.catalog_item:
         # None before the Storage Locations story adds a `storage` field,
         # which makes shelf_life_days pick the best location available.
         # Once that field exists this passes it and stays in that location.
         storage = getattr(self, "storage", None)
         days = self.catalog_item.shelf_life_days(storage)
 
         # 14 foods (salt, water, hard liquor) have no USDA duration at all,
         # so days is None and the item keeps an empty date.
         # expiration_status returns "Unknown" for that case.
         if days:
            self.date_expired = self.date_stored + timedelta(days=days)
 
      super().save(*args, **kwargs) #saves the item into the database
 
   def __str__(self):
      return f"Name: {self.catalog_item.name}, Stored: {self.date_stored}, Status: {self.expiration_status}"

