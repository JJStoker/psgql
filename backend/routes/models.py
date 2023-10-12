from django.db import models
from django.contrib.gis.db.models import PointField
from django.contrib.auth.models import User


class PointOfInterest(models.Model):
    location = PointField(srid=4326, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.notes}'

class Route(models.Model):
    owner = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    points = models.ManyToManyField(PointOfInterest)

    def __str__(self) -> str:
        return f'{self.name}'
