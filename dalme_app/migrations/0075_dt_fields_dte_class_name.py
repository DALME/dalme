# Generated by Django 2.1.7 on 2019-05-10 20:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0074_dt_fields_dt_width'),
    ]

    operations = [
        migrations.AddField(
            model_name='dt_fields',
            name='dte_class_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]