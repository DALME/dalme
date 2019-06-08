# Generated by Django 2.1.7 on 2019-05-24 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0098_tag'),
    ]

    operations = [
        migrations.RenameField(
            model_name='identity_phrase',
            old_name='transcription_id',
            new_name='transcription',
        ),
        migrations.RenameField(
            model_name='object_phrase',
            old_name='transcription_id',
            new_name='transcription',
        ),
        migrations.RenameField(
            model_name='source_pages',
            old_name='page_id',
            new_name='page',
        ),
        migrations.RenameField(
            model_name='source_pages',
            old_name='source_id',
            new_name='source',
        ),
        migrations.RenameField(
            model_name='source_pages',
            old_name='transcription_id',
            new_name='transcription',
        ),
        migrations.AddField(
            model_name='tag',
            name='tag_group',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
    ]