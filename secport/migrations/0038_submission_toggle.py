# Generated by Django 3.2.9 on 2022-01-24 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secport', '0037_group_num_posts'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='toggle',
            field=models.BooleanField(default=False),
        ),
    ]
