# Generated by Django 3.2.9 on 2022-01-21 06:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('secport', '0029_auto_20220121_0110'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Image',
            new_name='PostImage',
        ),
    ]