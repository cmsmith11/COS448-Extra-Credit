# Generated by Django 3.2.9 on 2022-01-29 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secport', '0040_auto_20220129_0239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='moderation',
            name='cw',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]