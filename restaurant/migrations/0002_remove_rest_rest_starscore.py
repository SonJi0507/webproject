# Generated by Django 3.2.5 on 2021-07-24 11:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rest',
            name='rest_starscore',
        ),
    ]
