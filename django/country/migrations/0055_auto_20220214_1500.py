# Generated by Django 2.1 on 2022-02-14 15:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('country', '0054_auto_20211202_1021'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='country',
            name='name_ar',
        ),
        migrations.RemoveField(
            model_name='countryoffice',
            name='name_ar',
        ),
        migrations.RemoveField(
            model_name='donor',
            name='name_ar',
        ),
    ]
