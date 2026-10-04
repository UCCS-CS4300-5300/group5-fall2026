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
   # This is the shared list of all the items
   # Below are going to be the fields of the items
   name = models.CharField(max_length=100, unique=True)
   category = models.CharField(max_length=50)
   # Positive BIg Integer field works with whole numbers and zero
   estimated_expiration_days = models.PositiveSmallIntegerField(default=7)

   def __str__(self):
      return self.name

class Pantry(models.Model):
   # This will be the main pantry model for the user

   # OneToOnefield makes sure the user can only have one pantry
   user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="pantry")

   name = models.CharField(max_length=100, default="Main Pantry")
   created_at = models.DateTimeField(default=timezone.now) # keeping track of when it was created

   def __str__(self):
      return f"{self.user.username}'s {self.name}"

class PantryItem(models.Model):
   # This will keep track of the item inside the user's pantry

   # foreign key is used for indicating which model it belongs to and
   # on the following field it makes sure there are can be duplicates
   pantry = models.ForeignKey(Pantry, on_delete=models.CASCADE, related_name="items")
   catalog_item = models.ForeignKey(GlobalCatalogItem, on_delete=models.CASCADE)


   quantity = models.PositiveSmallIntegerField(default=1)
   date_stored = models.DateField(default=timezone.now)

   date_expired = models.DateField(blank=True, null=True) # fields inside make it posible to accept empty inputs

   # TODO: Do we want to use a color border around the circle/image food item for drawing the user's Eye to the fact that the food is expiring?  

   @property
   # Will keep anapaula's expiration status function name
   def expiration_status(self): 
      # This function will help calculate the status of the expiration
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
   
   # This save methods makes it possible to have a safety net. In case there is 
   # an empty expiration date, then we will calculate the expiration date deadline.
   def save(self, *args, **kwargs):
      if not self.date_expired and self.catalog_item:
         self.date_expired = timezone.localdate() + timedelta(days=self.catalog_item.estimated_expiration_days)

      super().save(*args, **kwargs) #saves the item into the database

   def __str__(self):
      return f"Name: {self.catalog_item.name}, Stored: {self.date_stored}, Status: {self.expiration_status}"
