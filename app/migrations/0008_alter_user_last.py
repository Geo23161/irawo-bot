# Generated by Django 4.2.7 on 2024-10-18 14:41

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_alter_product_videos_alter_roommatch_why_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='last',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2024, 10, 18, 14, 41, 44, 877792, tzinfo=datetime.timezone.utc), null=True),
        ),
    ]
