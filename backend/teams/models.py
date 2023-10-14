from django.db import models

# Create your models here.

class Team(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    owner = models.ForeignKey("auth.User", db_index=True, on_delete=models.CASCADE)
    members = models.ManyToManyField('auth.User', related_name="teams")
