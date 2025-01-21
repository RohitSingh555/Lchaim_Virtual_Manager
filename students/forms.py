from django import forms
from .models import College, OrientationDate, StudentFile, StudentProfile, VolunteerLog



SHIFT_CHOICES = [
    ('Weekdays', 'Weekdays'),
    ('Weekends', 'Weekends'),
]

class StudentProfileForm(forms.ModelForm):
    shift_timing = forms.ChoiceField(choices=[('Morning', 'Morning'), ('Afternoon', 'Afternoon'), ('Night', 'Night'),('WeekendNight','WeekendNight'),('WeekendDay',"WeekendDay")], label="Shift Timing")
    lchaim_orientation_date = forms.ModelChoiceField(
        queryset=OrientationDate.objects.all(),
        empty_label="Select Orientation Date",
        label="Orientation Date"
    )
    class Meta:
        model = StudentProfile
        fields = [
            'first_name', 'last_name', 'phone', 'email', 'lchaim_training_completed',
            'college','start_date',
            'hours_requested', 'shift_requested', 'shift_timing', 'lchaim_orientation_date', 
            'skills_book_completed', 'police_check', 'med_docs', 'comments'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }
    def __init__(self, *args, **kwargs):
        # Check if the object instance is being passed (update case)
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        if instance is None:
            self.fields['start_date'].required = True
            self.fields['shift_timing'].required = True
        else:
            self.fields['start_date'].required = False
            self.fields['shift_timing'].required = False





class VolunteerLogForm(forms.ModelForm):
    class Meta:
        model = VolunteerLog
        fields = ['student', 'date', 'start_time', 'end_time', 'status', 'notes']
        
class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = ['name', 'address', 'contact_number', 'website']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class StudentFileForm(forms.ModelForm):
    class Meta:
        model = StudentFile
        fields = ['file']
       

class OrientationDateForm(forms.ModelForm):
    class Meta:
        model = OrientationDate
        fields = ['date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'placeholder': 'Optional description'}),
        }
        labels = {
            'date': 'Orientation Date',
            'description': 'Description (optional)',
        }