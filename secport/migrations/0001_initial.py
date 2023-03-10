# Generated by Django 3.2.9 on 2021-11-21 08:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.IntegerField(default=-1, primary_key=True, serialize=False)),
                ('content', models.CharField(max_length=10000)),
                ('type', models.CharField(max_length=20)),
                ('rep_secret', models.CharField(max_length=30)),
                ('oks', models.IntegerField(default=0)),
                ('not_oks', models.IntegerField(default=0)),
                ('status', models.CharField(max_length=20)),
                ('date_time_sub', models.DateTimeField(verbose_name='date submitted')),
                ('date_time_voted', models.DateTimeField(verbose_name='date fully voted')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.IntegerField(default=-1, primary_key=True, serialize=False)),
                ('confession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='secport.submission')),
            ],
        ),
    ]
