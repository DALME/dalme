# Generated by Django 3.1 on 2020-08-24 17:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0149_auto_20200820_1523'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='attribute',
            unique_together={('object_id', 'attribute_type', 'value_STR')},
        ),
    ]
