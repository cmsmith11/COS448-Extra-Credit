# Generated by Django 3.2.9 on 2021-12-29 04:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secport', '0014_group_repsecret'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='cw',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]