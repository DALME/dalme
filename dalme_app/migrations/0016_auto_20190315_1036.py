# Generated by Django 2.1.7 on 2019-03-15 14:36

import dalme_app.middleware
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0015_auto_20190315_0954'),
    ]

    operations = [
        migrations.CreateModel(
            name='Content_attributes',
            fields=[
                ('id', models.AutoField(db_index=True, primary_key=True, serialize=False, unique=True)),
                ('creation_username', models.CharField(blank=True, default=dalme_app.middleware.get_current_username, max_length=255, null=True)),
                ('creation_timestamp', models.DateTimeField(auto_now_add=True, null=True)),
                ('modification_username', models.CharField(blank=True, default=dalme_app.middleware.get_current_username, max_length=255, null=True)),
                ('modification_timestamp', models.DateTimeField(auto_now=True, null=True)),
                ('order', models.IntegerField(db_index=True)),
                ('attribute_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dalme_app.Attribute_type')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Content_type')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='content_type_x_attribute_type',
            name='attribute_type',
        ),
        migrations.RemoveField(
            model_name='content_type_x_attribute_type',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='Content_type_x_attribute_type',
        ),
        migrations.AddField(
            model_name='content_type',
            name='attribute_types',
            field=models.ManyToManyField(through='dalme_app.Content_attributes', to='dalme_app.Attribute_type'),
        ),
    ]
