# Generated by Django 3.2.9 on 2021-12-24 23:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secport', '0005_auto_20211224_1848'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='princetonsub',
            name='pton',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='content',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='dt_decided',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='dt_sub',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='not_oks',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='oks',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='rep_secret',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='status',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='type',
        ),
        migrations.RemoveField(
            model_name='testsub',
            name='test',
        ),
        #migrations.AlterField(
        #    model_name='submission',
        #    name='id',
        #    field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        #),
    ]
