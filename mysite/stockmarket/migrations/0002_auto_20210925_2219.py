# Generated by Django 3.2.5 on 2021-09-26 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stockmarket', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='macroeconomy',
            name='vix',
            field=models.TextField(default=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='stock',
            name='financials',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
    ]