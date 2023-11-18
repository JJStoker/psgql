import logging
import jwt

from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-u", "--user_id", help="user id", default=None)
        parser.add_argument("-t", "--team_ids", help="team ids", default=None)

    def get_claims(self, user):
        return dict(
            aud="postgraphile",
            exp=int((datetime.now() + timedelta(hours=1)).timestamp()),
            user_id=user.id,
            team_ids=",".join(map(str, user.teams.values_list('id', flat=True))),
            is_superuser=user.is_staff
        )

    def create_jwt(self, claims: dict[str, str | list | int | bool]):
        return jwt.encode(
            claims,
            "geheim",
            algorithm="HS256",
        )

    def handle(self, *args, **options):
        user = get_user_model().objects.get(id=options.get("user_id"))
        claims = self.get_claims(user)
        print (
            claims
        )
        print(
            self.create_jwt(claims)
        )
