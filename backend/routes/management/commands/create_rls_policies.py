import logging

from django.db.models import Model
from django.core.management.base import BaseCommand
from django.conf import settings

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('--create-role', action="store_true")
        parser.add_argument('--create-type', action="store_true")
        pass

    def create_roles(self, cursor):
        role_name = "user_role"
        cursor.execute(f"""
            DROP ROLE IF EXISTS {role_name};
            CREATE ROLE {role_name};
        """)

    def create_type(self, cursor):
        cursor.execute(f"""
            DROP TYPE IF EXISTS {settings.GRAPHILE_TOKEN_IDENTIFIER} CASCADE;
            CREATE TYPE {settings.GRAPHILE_TOKEN_IDENTIFIER} as (
                aud text,
                role text,
                exp integer,
                user_id integer
            );
            """)

    def create_user_roles(self, cursor):
        # Create RLS Policies
        role_name = "user_role"
        cursor.execute(f"""
        CREATE OR REPLACE FUNCTION current_user_id() returns integer as $$
        select nullif(current_setting('jwt.claims.user_id', true), '')::integer;
        $$ language sql stable;
        """)
        cursor.execute(f"""
        GRANT EXECUTE ON FUNCTION current_user_id TO {role_name};
        """)

        for model in [cls for cls in Model.__subclasses__() if hasattr(cls, "user")]:
            table_name = model._meta.db_table
            policy_name = f"{role_name}_rls"

            # RLS Policy SQL
            rls_policy_sql = f"""
            GRANT ALL ON TABLE {table_name} TO {role_name};
            CREATE POLICY {policy_name} ON {table_name}
            FOR ALL TO {role_name} 
            USING ("user_id" = current_user_id()) 
            WITH CHECK ("user_id" = current_user_id());
            """

            # Activating RLS SQL
            activate_rls_sql = f"""
            ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
            """
            
            # Debugging: Print the SQL being executed
            print("Executing Activation SQL: ", activate_rls_sql.strip())
            print("Executing RLS Policy SQL: ", rls_policy_sql.strip())
            
            # Execute SQL
            try:
                cursor.execute(f"SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND policyname = '{policy_name}' AND tablename = '{table_name}';")
                if cursor.fetchone():
                    cursor.execute(f"DROP POLICY {policy_name} on {table_name};")
                cursor.execute(rls_policy_sql)
                cursor.execute(activate_rls_sql)
                self.stdout.write(self.style.SUCCESS(f'Successfully created RLS for {table_name}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error creating RLS for {table_name}: {str(e)}'))

    def handle(self, *args, **options):
        print (options)
        
        with connection.cursor() as cursor:
            if options.get("create_role"): self.create_roles(cursor)
            if options.get("create_type"): self.create_type(cursor)
            self.create_user_roles(cursor)
