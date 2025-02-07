import json
from django import forms
from .models import College, OrientationDate, StudentFile, StudentProfile, VolunteerLog



SHIFT_CHOICES = [
    ('Weekdays', 'Weekdays'),
    ('Weekends', 'Weekends'),
]
WEEKDAYS_CHOICES = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


class StudentProfileForm(forms.ModelForm):
    shift_timing = forms.ChoiceField(choices=[('Morning', 'Morning'), ('Afternoon', 'Afternoon'), ('Night', 'Night'),('WeekendNight','WeekendNight'),('WeekendDay',"WeekendDay")], label="Shift Timing")
    lchaim_orientation_date = forms.ModelChoiceField(
        queryset=OrientationDate.objects.all(),
        empty_label="Select Orientation Date",
        label="Orientation Date"
    )
    weekdays_selected = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),  # Hide it since JS will populate it
        label="Preferred Weekdays"
    )

    def clean_weekdays_selected(self):
        """Ensure the value is a valid JSON string representing a key-value dictionary"""
        data = self.cleaned_data.get("weekdays_selected", "")

        if not data:
            return {}

        try:
            selected_weekdays = json.loads(data)  # Convert JSON string to dict
            # Ensure all keys and values are valid
            cleaned_weekdays = {
                key: WEEKDAYS_CHOICES[key]
                for key in selected_weekdays.keys()
                if key in WEEKDAYS_CHOICES and selected_weekdays[key] == WEEKDAYS_CHOICES[key]
            }
            return cleaned_weekdays
        except (json.JSONDecodeError, KeyError, ValueError):
            raise forms.ValidationError("Invalid weekdays format. Ensure it is a valid JSON dictionary.")


    college = forms.ModelChoiceField(
        queryset=College.objects.all(),
        empty_label="Select College",  # Default empty label
        required=True,  # Allow null selection
        label="College"
    )
    class Meta:
        model = StudentProfile
        fields = [
            'first_name', 'last_name', 'phone', 'email', 'lchaim_training_completed',
            'college','start_date',
            'hours_requested', 'shift_requested', 'shift_timing', 'lchaim_orientation_date', 'weekdays_selected',
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