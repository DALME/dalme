# Generated by Django 2.2.1 on 2019-05-31 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0101_auto_20190528_0914'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dt_fields',
            name='dte_type',
            field=models.CharField(choices=[('autoComplete', 'autoComplete'), ('checkbox', 'checkbox'), ('chosen', 'chosen'), ('date', 'date'), ('datetime', 'datetime'), ('hidden', 'hidden'), ('multi-chosen', 'multi-chosen'), ('multi-selectize', 'multi-selectize'), ('password', 'password'), ('radio', 'radio'), ('readonly', 'readonly'), ('select', 'select'), ('selectize', 'selectize'), ('text', 'text'), ('textarea', 'textarea'), ('upload', 'upload'), ('uploadMany', 'uploadMany')], default=None, max_length=55, null=True),
        ),
    ]