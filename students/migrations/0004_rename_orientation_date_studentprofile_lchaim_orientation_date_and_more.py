# Generated by Django 5.1.4 on 2024-12-14 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_alter_studentprofile_email_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='studentprofile',
            old_name='orientation_date',
            new_name='lchaim_orientation_date',
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='hours_requested',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='lchaim_training_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='med_docs',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='phone',
            field=models.CharField(default='0000000000', max_length=15),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='shift_requested',
            field=models.CharField(choices=[('Weekdays', 'Weekdays'), ('Weekends', 'Weekends')], default='Weekdays', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='skills_book_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='school',
            field=models.CharField(choices=[('Toronto Business', 'Toronto Business'), ('School A', 'School A'), ('School B', 'School B'), ('School C', 'School C'), ('School D', 'School D')], max_length=100),
        ),
    ]
