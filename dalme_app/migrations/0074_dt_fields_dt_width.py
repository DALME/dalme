# Generated by Django 2.1.7 on 2019-05-10 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0073_auto_20190510_1638'),
    ]

    operations = [
        migrations.AddField(
            model_name='dt_fields',
            name='dt_width',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
