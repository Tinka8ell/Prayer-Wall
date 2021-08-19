# Generated by Django 3.1.2 on 2021-07-29 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_auto_20210729_0822'),
    ]

    operations = [
        migrations.AddField(
            model_name='slot',
            name='watch',
            field=models.IntegerField(choices=[(0, 'Hourly'), (1, 'Morning'), (2, 'Afternoon'), (3, 'Evening'), (4, 'Night'), (5, 'All Day')], default=0),
        ),
        migrations.DeleteModel(
            name='DaySlot',
        ),
    ]
