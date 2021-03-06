# Generated by Django 3.2.5 on 2021-09-03 07:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MacroEconomy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.TextField()),
                ('fed_rate', models.TextField()),
                ('longterm_treasury_yield', models.TextField()),
                ('inflation_rate', models.TextField()),
                ('unemployment_rate', models.TextField()),
                ('gdp', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.TextField()),
                ('ticker', models.TextField()),
                ('stock_price', models.TextField()),
                ('dividends', models.TextField()),
                ('volume', models.TextField()),
                ('stock_splits', models.TextField()),
                ('interval', models.TextField()),
                ('macro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stockmarket.macroeconomy')),
            ],
        ),
    ]
