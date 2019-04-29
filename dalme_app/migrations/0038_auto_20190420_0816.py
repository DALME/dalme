# Generated by Django 2.1.7 on 2019-04-20 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0037_dt_fields_dte_opts'),
    ]

    operations = [
        migrations.AddField(
            model_name='dt_fields',
            name='filter_mode',
            field=models.CharField(max_length=55, null=True),
        ),
        migrations.AddField(
            model_name='dt_fields',
            name='filter_type',
            field=models.CharField(max_length=55, null=True),
        ),
        migrations.AddField(
            model_name='dt_fields',
            name='is_filter',
            field=models.BooleanField(default=False),
        ),
    ]