# Generated by Django 3.1.2 on 2021-02-17 21:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0004_ticket_assigned_to'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together={('tag', 'object_id')},
        ),
    ]
