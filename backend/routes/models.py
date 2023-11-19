from django.db import models
from django.contrib.gis.db.models import PointField

from src.scanner import Claims, Roles, rls



@rls((Claims.USER, 'owner_id', '"shared" = true'),)
class PointOfInterest(models.Model):
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="pois", null=True, blank=True)
    location = PointField(srid=4326, null=True)
    notes = models.TextField(blank=True, null=True)
    shared = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.notes}'

@rls((Claims.USER, 'user_id'), (Claims.TEAMS, 'team_id'),)
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
