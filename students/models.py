from django.db import models
from datetime import datetime, date

class College(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class StudentProfile(models.Model):
    SHIFT_CHOICES = [
        ('Weekdays', 'Weekdays'),
        ('Weekends', 'Weekends'),
    ]  # Define SHIFT_CHOICES at the class level

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, default='0000000000')
    email = models.EmailField(unique=True)
    school = models.CharField(max_length=100)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    lchaim_training_completed = models.BooleanField(default=False)
    police_check = models.BooleanField(default=False)
    med_docs = models.BooleanField(default=False)
    hours_requested = models.IntegerField(null=True)
    hours_completed = models.PositiveIntegerField(default=0)
    shift_requested = models.CharField(max_length=10, choices=SHIFT_CHOICES)  # Use SHIFT_CHOICES here
    lchaim_orientation_date = models.DateField(null=True)
    skills_book_completed = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ('Training', 'Training'),
            ('Graduated', 'Graduated'),
        ],
        default='Training'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class VolunteerLog(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="volunteer_logs")
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)  
    end_time = models.TimeField(null=True, blank=True)  
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')], default='Absent')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Log for {self.student} on {self.date}"

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            duration = datetime.combine(date.today(), self.end_time) - datetime.combine(date.today(), self.start_time)
            self.hours_worked = duration.total_seconds() / 3600
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['date']

class StudentFile(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="student_files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} uploaded for {self.student.first_name} {self.student.last_name}"

    class Meta:
        ordering = ['uploaded_at']