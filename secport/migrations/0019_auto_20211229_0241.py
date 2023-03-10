# Generated by Django 3.2.9 on 2021-12-29 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secport', '0018_auto_20211229_0151'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='dislikes',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='likes',
        ),
        migrations.AddField(
            model_name='submission',
            name='quality',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='moderation',
            name='cw',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='moderation',
            name='quality',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='submission',
            name='cw',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
