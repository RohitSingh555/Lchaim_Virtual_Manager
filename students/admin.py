from django.contrib import admin
from .models import StudentProfile, College, Shift, VolunteerLog, StudentFile

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'phone',
        'email',
        'school',
        'lchaim_training_completed',
        'police_check',
        'med_docs',
        'hours_requested',
        'shift_requested',
        'lchaim_orientation_date',
        'skills_book_completed',
        'comments'
    )
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'school')
    list_filter = ('school', 'shift_requested', 'lchaim_training_completed', 'police_check', 'skills_book_completed')

admin.site.register(College)
admin.site.register(Shift)
admin.site.register(VolunteerLog)
admin.site.register(StudentFile)
