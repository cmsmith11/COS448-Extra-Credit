# Generated by Django 3.2.9 on 2022-01-21 06:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secport', '0028_auto_20220111_2338'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img', models.ImageField(upload_to='images/')),
            ],
        ),
        migrations.AlterField(
            model_name='submission',
            name='sub_num',
            field=models.CharField(default='N/A', max_length=20),
        ),
    ]
