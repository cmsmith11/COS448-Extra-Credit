# Generated by Django 3.2.9 on 2021-11-27 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secport', '0002_auto_20211125_1936'),
    ]

    operations = [
        migrations.RenameField(
            model_name='submission',
            old_name='date_time_voted',
            new_name='dt_decided',
        ),
        migrations.RenameField(
            model_name='submission',
            old_name='date_time_sub',
            new_name='dt_sub',
        ),
        migrations.AlterField(
            model_name='submission',
            name='id',
            field=models.CharField(max_length=50, primary_key=True, serialize=False),
        ),
    ]
