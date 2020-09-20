# Generated by Django 3.1 on 2020-09-13 17:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dalme_app', '0160_auto_20200911_1052'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='languagereference',
            name='lang_type',
        ),
        migrations.AlterField(
            model_name='languagereference',
            name='type',
            field=models.IntegerField(choices=[(1, 'Language'), (2, 'Dialect')]),
        ),
        migrations.AlterField(
            model_name='source',
            name='parent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_query_name='source_children', to='dalme_app.source'),
        ),
    ]
