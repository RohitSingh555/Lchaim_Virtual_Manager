# Generated by Django 4.2.17 on 2024-12-14 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('school', models.CharField(choices=[('engineering', 'Engineering'), ('management', 'Management'), ('arts', 'Arts')], max_length=20)),
                ('police_check', models.BooleanField(default=False)),
                ('orientation_date', models.DateField()),
            ],
        ),
    ]