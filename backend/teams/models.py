from django.db import models

from src.scanner import Claims, rls

# Create your models here.

@rls((Claims.USER, 'owner_id'), (Claims.TEAMS, 'members__id'),)
class Team(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    owner = models.ForeignKey("auth.User", db_index=True, on_delete=models.CASCADE)
    members = models.ManyToManyField('auth.User', related_name="teams")
