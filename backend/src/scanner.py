

import enum
from typing import Optional, Tuple


class Roles(enum.StrEnum):
    USER = 'user_role'

class Claims(enum.StrEnum):
    USER = 'user_id'
    TEAMS = 'team_ids'

def rls(*policies: Tuple[Claims, str, str | None]):
    def handle_registration(cls):
        assert all(map(lambda policy: policy[0] in Claims, policies)), f'Malformed policies in {cls}: {policies}'
        cls.rls_policies = policies
        return cls
    return handle_registration
