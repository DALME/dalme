# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-08-05 13:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0014_remove_par_tokens_span_end'),
    ]

    operations = [
        migrations.AddField(
            model_name='par_tokens',
            name='span_end',
            field=models.IntegerField(),
            preserve_default=False,
        ),
    ]
