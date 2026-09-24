from django.db import models
from django.contrib.auth.models import User # Django built-in user model
from django.utils import timezone # Useful for date tracking


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
   date_expired = models.DateField()

   @property
   # Will keep anapaula's expiration status function name
   def expiration_status(self): 
      # This function will help calculate the status of the expiration
      today = timezone.localdate() # made it localdate for more accurate date representation
      # Expired if more than the date it expired
      if today >= self.date_expired: #Fixed
         return "Expired"
      
      # For letting the user know if its 3 days before expiring (subject to change)
      elif 0 < (self.date_expired - today).days <= 3:
         return "Expiring Soon"
      # Otherwise it is categorized as fresh for simplicity
      return "Fresh"

   def __str__(self):
      return f"Name: {self.catalog_item.name}, Stored: {self.date_stored}, Expired: {self.expiration_status}"



"""
WILL KEEP THIS CODE AS REFERENCE FOR THE INTIAL APPROACH

class StarterItem(models.Model):
 title=models.CharField(max_length=120)
 description=models.TextField(blank=True)
 is_active=models.BooleanField(default=True)
 def __str__(self): return self.title
    
class Food(models.Model):

    name = models.CharField(max_length = 100)
    #date food is brought into the pantry
    #made it store the date that the item is created
    #non-editable date (wanna fix?)
    # (Jorge's take) I think i will make it so instead of having a hard date, it can check today
    date_stored = models.DateField(auto_now_add = True)
    #stored as yyyy-mm-dd
    date_expired = models.DateField()
    expiration_status = models.CharField(max_length = 50)

    def __str__(self):
        string_name = f"Name: {self.name}"
        string_date_stored = f"Date Stored: {self.name_stored}"
        string_date_expired = f"Expiration Date: {self.date_expired}"
        string_expiration_status = f"Expiration Status: {self.expiration_status"

        return f"{string_name}, {string_date_stored}, {string_date_expired},{string_expiration_status}."
"""