# Generated by Django 5.0.4 on 2024-10-29 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataapp', '0005_remove_catrackingdata_otherdata1_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catrackingdata',
            name='rawJson',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='srtrackingdata',
            name='rawJson',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
