from django.db import models

class StudentProfile(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, default='0000000000')
    email = models.EmailField(unique=True)
    school = models.CharField(max_length=100, choices=[
        ('Toronto Business', 'Toronto Business'),
        ('School A', 'School A'),
        ('School B', 'School B'),
        ('School C', 'School C'),
        ('School D', 'School D'),
    ])
    lchaim_training_completed = models.BooleanField(default=False)
    police_check = models.BooleanField(default=False)
    med_docs = models.BooleanField(default=False)
    hours_requested = models.PositiveIntegerField(null=True, blank=True)
    shift_requested = models.CharField(max_length=10, choices=[
        ('Weekdays', 'Weekdays'),
        ('Weekends', 'Weekends'),
    ])
    lchaim_orientation_date = models.DateField()
    skills_book_completed = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
