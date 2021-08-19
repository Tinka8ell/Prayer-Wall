# Generated by Django 3.1.2 on 2021-07-29 08:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DaySlot',
            fields=[
                ('slot_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='bookings.slot')),
                ('watch', models.IntegerField(choices=[(0, 'All Day'), (1, 'Morning'), (2, 'Afternoon'), (3, 'Evening'), (4, 'Night')])),
            ],
            bases=('bookings.slot',),
        ),
        migrations.AddField(
            model_name='event',
            name='isDaily',
            field=models.BooleanField(default=False),
        ),
    ]