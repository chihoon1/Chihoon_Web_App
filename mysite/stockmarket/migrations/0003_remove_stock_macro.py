# Generated by Django 3.2.5 on 2021-10-04 01:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stockmarket', '0002_auto_20210925_2219'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stock',
            name='macro',
        ),
    ]