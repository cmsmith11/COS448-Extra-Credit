# Generated by Django 4.0.4 on 2022-06-14 03:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secport', '0041_alter_moderation_cw'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='color1',
            field=models.CharField(default='#ffffff', max_length=7),
        ),
        migrations.AddField(
            model_name='group',
            name='color2',
            field=models.CharField(default='#000000', max_length=7),
        ),
        migrations.AddField(
            model_name='group',
            name='color3',
            field=models.CharField(default='#000000', max_length=7),
        ),
        migrations.AddField(
            model_name='group',
            name='color4',
            field=models.CharField(default='#dddddd', max_length=7),
        ),
    ]
