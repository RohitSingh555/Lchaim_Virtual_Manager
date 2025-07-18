from django.contrib.auth.models import User
from django.db import models
from datetime import datetime, date, timedelta


class College(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class OrientationDate(models.Model):
    date = models.DateField(unique=True)
    start_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.date.strftime('%Y-%m-%d')

class Shift(models.Model):
    SHIFT_TYPES = [
        ('Morning', 'Morning (7 AM - 3 PM)'),
        ('Afternoon', 'Afternoon (3 PM - 11 PM)'),
        ('Night', 'Night (9 PM - 6 AM)'),
        ('WeekendDay', 'Weekend Day (7 AM - 9 PM)'),
        ('WeekendNight', 'Weekend Night (9 PM - 6 AM)'),
    ]

    type = models.CharField(max_length=12, choices=SHIFT_TYPES, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_students = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.type} ({self.start_time} - {self.end_time})"


class StudentProfile(models.Model):
    SHIFT_CHOICES = [
        ('Weekdays', 'Weekdays'),
        ('Weekends', 'Weekends'),
    ]
    
    WEEKDAYS_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, default='')
    email = models.EmailField(unique=True)
    college_contact_person = models.TextField(default='', blank=True)
    college_contact_person_email = models.CharField(max_length=100, default='')
    school = models.CharField(max_length=100)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    lchaim_training_completed = models.BooleanField(default=False)
    police_check = models.BooleanField(default=False)
    med_docs = models.BooleanField(default=False)
    hours_requested = models.IntegerField(null=True)
    hours_completed = models.PositiveIntegerField(default=0)
    shift_requested = models.CharField(max_length=10, choices=SHIFT_CHOICES)
    weekdays_selected = models.TextField(null=True, blank=True)
    assigned_shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    lchaim_orientation_date = models.ForeignKey(OrientationDate, on_delete=models.SET_NULL, null=True, blank=True)
    skills_book_completed = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=[('Training', 'Training'), ('Graduated', 'Graduated')],
        default='Training'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"{self.first_name} {self.last_name}"

    def calculate_end_date(self):
        if self.start_date and self.hours_requested:
            total_days = (self.hours_requested // 8) + 1 
            self.end_date = self.start_date + timedelta(days=total_days)


class VolunteerLog(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="volunteer_logs")
    date = models.DateField()
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')], default='Absent')
    notes = models.TextField(blank=True, null=True)
    extended = models.BooleanField(default=False)

    def __str__(self):
        return f"Log for {self.student} on {self.date}"

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


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("profile_created", "Profile Created"),
        ("profile_updated", "Profile Updated"),
        ("profile_deleted", "Profile Deleted"),
        # Add more as needed
    ]
    action_type = models.CharField(max_length=32, choices=ACTION_CHOICES)
    profile = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='activity_logs')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    shift_type = models.CharField(max_length=64, blank=True, null=True)
    shift_capacity = models.PositiveIntegerField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    extra_data = models.JSONField(blank=True, null=True, default=dict)

    def __str__(self):
        return f"{self.get_action_type_display()} for {self.profile} at {self.created_at}"

