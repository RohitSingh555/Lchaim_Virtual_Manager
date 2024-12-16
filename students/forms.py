from django import forms
from .models import StudentProfile, VolunteerLog

SCHOOL_CHOICES = [
    ('Toronto Business', 'Toronto Business'),
    ('School A', 'School A'),
    ('School B', 'School B'),
    ('School C', 'School C'),
    ('School D', 'School D'),
]

SHIFT_CHOICES = [
    ('Weekdays', 'Weekdays'),
    ('Weekends', 'Weekends'),
]

class StudentProfileForm(forms.ModelForm):
    school = forms.ChoiceField(choices=SCHOOL_CHOICES)
    shift_requested = forms.ChoiceField(choices=SHIFT_CHOICES)

    class Meta:
        model = StudentProfile
        fields = [
            'first_name', 'last_name', 'phone', 'email', 'lchaim_training_completed', 'school', 
             'hours_requested', 'shift_requested', 
            'lchaim_orientation_date', 'skills_book_completed', 'police_check', 'med_docs','comments'
        ]
        widgets = {
            'lchaim_orientation_date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }

class VolunteerLogForm(forms.ModelForm):
    class Meta:
        model = VolunteerLog
        fields = ['student', 'date', 'start_time', 'end_time', 'status', 'notes']