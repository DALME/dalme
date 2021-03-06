# Generated by Django 3.1.2 on 2021-01-18 16:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_currentuser.middleware
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dalme_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedSearch',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('creation_timestamp', models.DateTimeField(auto_now_add=True, null=True)),
                ('modification_timestamp', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
                ('search', models.JSONField()),
                ('creation_user', models.ForeignKey(default=django_currentuser.middleware.get_current_user, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dalme_app_savedsearch_creation', to=settings.AUTH_USER_MODEL)),
                ('modification_user', models.ForeignKey(default=django_currentuser.middleware.get_current_user, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dalme_app_savedsearch_modification', to=settings.AUTH_USER_MODEL)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dalme_app_savedsearch_related', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
