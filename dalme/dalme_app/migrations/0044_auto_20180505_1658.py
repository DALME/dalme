# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-05-05 20:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0043_auto_20180505_1646'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attributes',
            name='content_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Sources'),
        ),
        migrations.AlterField(
            model_name='attributes_date',
            name='attribute_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Attributes'),
        ),
        migrations.AlterField(
            model_name='attributes_dbr',
            name='attribute_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Attributes'),
        ),
        migrations.AlterField(
            model_name='attributes_int',
            name='attribute_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Attributes'),
        ),
        migrations.AlterField(
            model_name='attributes_str',
            name='attribute_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Attributes'),
        ),
        migrations.AlterField(
            model_name='attributes_txt',
            name='attribute_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Attributes'),
        ),
        migrations.AlterField(
            model_name='content_types_x_attribute_types',
            name='attribute_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Attribute_types'),
        ),
        migrations.AlterField(
            model_name='content_types_x_attribute_types',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Content_types'),
        ),
        migrations.AlterField(
            model_name='headwords',
            name='concept_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Concepts'),
        ),
        migrations.AlterField(
            model_name='identity_phrases',
            name='transcription_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Transcriptions'),
        ),
        migrations.AlterField(
            model_name='identity_phrases_x_entities',
            name='identity_phrase_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Identity_phrases'),
        ),
        migrations.AlterField(
            model_name='object_attributes',
            name='object_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Objects'),
        ),
        migrations.AlterField(
            model_name='object_phrases',
            name='transcription_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Transcriptions'),
        ),
        migrations.AlterField(
            model_name='objects',
            name='object_phrase_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Object_phrases'),
        ),
        migrations.AlterField(
            model_name='pages',
            name='source_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Sources'),
        ),
        migrations.AlterField(
            model_name='tokens',
            name='object_phrase_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Object_phrases'),
        ),
        migrations.AlterField(
            model_name='tokens',
            name='word_form_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Word_forms'),
        ),
        migrations.AlterField(
            model_name='transcriptions',
            name='source_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Sources'),
        ),
        migrations.AlterField(
            model_name='word_forms',
            name='headword_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dalme_app.Headwords'),
        ),
    ]
