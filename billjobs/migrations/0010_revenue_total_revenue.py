# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-07 15:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billjobs', '0009_revenue'),
    ]

    operations = [
        migrations.AddField(
            model_name='revenue',
            name='total_revenue',
            field=models.FloatField(default=0.0),
        ),
    ]