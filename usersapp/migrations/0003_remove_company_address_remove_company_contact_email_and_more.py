# Generated by Django 5.0.4 on 2024-10-24 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usersapp', '0002_alter_customuser_role'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='address',
        ),
        migrations.RemoveField(
            model_name='company',
            name='contact_email',
        ),
        migrations.RemoveField(
            model_name='company',
            name='contact_phone',
        ),
        migrations.AddField(
            model_name='company',
            name='interior',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='company',
            name='omni',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='company',
            name='wh',
            field=models.BooleanField(default=False),
        ),
    ]
