# Generated by Django 3.2.21 on 2023-09-22 13:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='is_stuff',
            new_name='is_staff',
        ),
    ]
