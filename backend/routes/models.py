from django.db import models
from django.contrib.gis.db.models import PointField


class PointOfInterest(models.Model):
    location = PointField(srid=4326, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.notes}'

class Route(models.Model):
    user = models.ForeignKey("auth.User", db_index=True, on_delete=models.SET_NULL, related_name="routes", null=True, blank=True)
    team = models.ForeignKey("teams.Team", db_index=True, on_delete=models.SET_NULL, related_name="routes", null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    points = models.ManyToManyField(PointOfInterest)

    def __str__(self) -> str:
        return f'{self.name}'

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(team__isnull=False),
                name="always_linked",
                violation_error_message="Route must always be linked to either team or user"
            ),
        ]
