import logging
from django.apps import apps

from django.db.models import Model
from django.conf import settings

from django.core.management.base import BaseCommand
from django.db import connection
from routes.models import Route

from src.scanner import Claims, Roles


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def create_type(self, cursor):
        cursor.execute(f"""DROP TYPE IF EXISTS {settings.GRAPHILE_TOKEN_IDENTIFIER} CASCADE;""")
        cursor.execute(f"""
            CREATE TYPE {settings.GRAPHILE_TOKEN_IDENTIFIER} as (
                aud text,
                role text,
                exp integer,
                user_id integer,
                team_ids text
            );
        """)

    def create_roles(self, cursor):
        for role_name in Roles:
            try:
                cursor.execute(f"""
                    DROP OWNED BY {role_name};
                    DROP ROLE IF EXISTS {role_name};
                    CREATE ROLE {role_name};
                """)
            except:
                print(f"role already created {role_name}")

    def create_current_user_id(self, cursor):
        cursor.execute(f"""
        CREATE OR REPLACE FUNCTION current_user_id() returns integer as $$
        select nullif(current_setting('jwt.claims.user_id', true), '')::integer;
        $$ language sql stable;
        """)
        for role_name in Roles:
            cursor.execute(f"""GRANT EXECUTE ON FUNCTION current_user_id TO {role_name};""")

    def create_current_team_ids(self, cursor):
        cursor.execute(f"""
            CREATE OR REPLACE FUNCTION current_team_ids() RETURNS integer[] AS $$
            BEGIN
                RETURN string_to_array(nullif(current_setting('jwt.claims.team_ids', true), ''), ',')::integer[];
            END;
            $$ LANGUAGE plpgsql STABLE;
        """)
        for role_name in Roles:
            cursor.execute(f"""GRANT EXECUTE ON FUNCTION current_team_ids TO {role_name};""")

    def create_is_superuser(self, cursor):
        cursor.execute(f"""
        CREATE OR REPLACE FUNCTION is_superuser() returns BOOLEAN as $$
        select nullif(current_setting('jwt.claims.is_superuser', true), '')::BOOLEAN;
        $$ language sql stable;
        """)
        for role_name in Roles:
            cursor.execute(f"""GRANT EXECUTE ON FUNCTION is_superuser TO {role_name};""")

    def disable_rls(self, cursor):
        cursor.execute("""
        SELECT 'ALTER TABLE ' || quote_ident(table_schema) || '.' || quote_ident(table_name) || ' DISABLE ROW LEVEL SECURITY;'
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_type = 'BASE TABLE';
        """)
        commands = cursor.fetchall()
        # Execute each command
        for cmd in commands:
            cursor.execute(cmd[0])
        self.stdout.write(self.style.SUCCESS(f'Successfully disabled rls'))

    def grant_all_to_role(self, cursor, table_name, role_name):
        policy_name = f'{role_name}_all_rls'
        rls_policy_sql = f"""
        GRANT ALL ON TABLE {table_name} TO {role_name};
        CREATE POLICY {policy_name} ON {table_name}
        FOR ALL TO {role_name}
        USING (true);
        """
        try:
            cursor.execute(f"SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND policyname = '{policy_name}' AND tablename = '{table_name}';")
            if cursor.fetchone():
                cursor.execute(f"DROP POLICY {policy_name} on {table_name};")
            cursor.execute(rls_policy_sql)
            self.stdout.write(self.style.SUCCESS(f'Successfully created RLS for {table_name}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error creating RLS for {table_name}: {str(e)}'))

    def enable_rls_for_table(self, cursor, table_name):
        # Activating RLS SQL
        cursor.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
        self.stdout.write(self.style.SUCCESS(f'Successfully enabled RLS for {table_name}'))

    def add_user_check_to_role(self, cursor, table_name, user_column, exception = None, role_name = "user_role"):
        # RLS Policy SQL
        policy_name = f"{role_name}_rls"
        rls_policy_sql = f"""
        GRANT ALL ON TABLE {table_name} TO {role_name};
        CREATE POLICY {policy_name} ON {table_name}
        FOR ALL TO {role_name} 
        USING (is_superuser() or "{user_column}" = current_user_id()) 
        WITH CHECK (is_superuser() or "{user_column}" = current_user_id() {f'or {exception}' if exception else ''});
        """

        # Debugging: Print the SQL being executed
        print("Executing RLS Policy SQL: ", rls_policy_sql.strip())
        # Execute SQL
        try:
            cursor.execute(f"SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND policyname = '{policy_name}' AND tablename = '{table_name}';")
            if cursor.fetchone():
                cursor.execute(f"DROP POLICY {policy_name} on {table_name};")
            cursor.execute(rls_policy_sql)
            self.stdout.write(self.style.SUCCESS(f'Successfully created RLS for {table_name}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error creating RLS for {table_name}: {str(e)}'))

    def add_team_check_to_role(self, cursor, table_name, team_column, exception = None, role_name = "user_role"):
        policy_name = f"{role_name}_team_rls"
        # RLS Policy SQL
        rls_policy_sql = f"""
        GRANT ALL ON TABLE {table_name} TO {role_name};
        CREATE POLICY {policy_name} ON {table_name}
        FOR SELECT TO {role_name}
        USING (is_superuser() or "{team_column}" = ANY(current_team_ids() {f'or {exception}' if exception else ''}));
        """

        print("Executing RLS Policy SQL: ", rls_policy_sql.strip())
        
        # Execute SQL
        try:
            cursor.execute(f"SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND policyname = '{policy_name}' AND tablename = '{table_name}';")
            if cursor.fetchone():
                cursor.execute(f"DROP POLICY {policy_name} on {table_name};")
            cursor.execute(rls_policy_sql)
            self.stdout.write(self.style.SUCCESS(f'Successfully created RLS for {table_name}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error creating RLS for {table_name}: {str(e)}'))

    def handle(self, *args, **options):
        print (options)
        with connection.cursor() as cursor:
            self.create_type(cursor)
            self.create_roles(cursor)
            self.create_current_user_id(cursor)
            self.create_current_team_ids(cursor)
            self.create_is_superuser(cursor)
            self.disable_rls(cursor)

            for model in filter(lambda cls: hasattr(cls, 'rls_policies'), apps.get_models()):
                table_name = model._meta.db_table
                self.enable_rls_for_table(cursor, table_name)
                for role in Roles:
                    for m2m in model._meta.many_to_many:
                        self.grant_all_to_role(cursor, m2m.remote_field.through._meta.db_table, role)
                for policy in filter(lambda policy: policy[0] in Claims, model.rls_policies):
                    claim = policy[0]
                    column = policy[1]
                    exception = policy[2] if len(policy) > 2 else None
                    if "__" in column:
                        # todo: we need to be able to join the other table to fetch through
                        pass
                    elif claim == Claims.USER:
                        self.add_user_check_to_role(cursor, table_name, column, exception)
                    elif claim == Claims.TEAMS:
                        self.add_team_check_to_role(cursor, table_name, column, exception)
