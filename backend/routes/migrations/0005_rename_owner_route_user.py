# Generated by Django 5.0a1 on 2023-10-13 18:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0004_alter_route_owner'),
    ]

    operations = [
        migrations.RenameField(
            model_name='route',
            old_name='owner',
            new_name='user',
        ),
    ]
