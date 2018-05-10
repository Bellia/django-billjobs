# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-07 22:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billjobs', '0010_revenue_total_revenue'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='billjobs.Service')),
            ],
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='april',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='august',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='december',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='february',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='january',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='july',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='june',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='march',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='may',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='november',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='october',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='september',
        ),
        migrations.RemoveField(
            model_name='revenue',
            name='total_revenue',
        ),
    ]
