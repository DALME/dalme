# Generated by Django 2.1.7 on 2019-03-23 14:33

import dalme_app.middleware
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0023_auto_20190322_1616'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeReference',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('creation_username', models.CharField(blank=True, default=dalme_app.middleware.get_current_username, max_length=255, null=True)),
                ('creation_timestamp', models.DateTimeField(auto_now_add=True, null=True)),
                ('modification_username', models.CharField(blank=True, default=dalme_app.middleware.get_current_username, max_length=255, null=True)),
                ('modification_timestamp', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
                ('short_name', models.CharField(max_length=55)),
                ('description', models.TextField()),
                ('data_type', models.CharField(max_length=15)),
                ('source', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
