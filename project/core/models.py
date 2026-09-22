from django.db import models
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
