# Generated by Django 5.1.4 on 2024-12-16 18:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0004_rename_orientation_date_studentprofile_lchaim_orientation_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='hours_completed',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name='VolunteerLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('hours_worked', models.DecimalField(decimal_places=2, max_digits=5)),
                ('notes', models.TextField(blank=True, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='volunteer_logs', to='students.studentprofile')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
    ]
