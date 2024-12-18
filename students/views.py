from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from .models import StudentProfile, VolunteerLog
from django.db.models import Sum
from django.http import JsonResponse
from .forms import StudentProfileForm, VolunteerLogForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth import login, logout, authenticate
from datetime import timedelta
import json
from decimal import Decimal
def admin_required(function):
    def wrap(request, *args, **kwargs):
        if not request.user.groups.filter(name='Admin').exists():
            return redirect('student_profile_list') 
        return function(request, *args, **kwargs)
    return wrap

def school_required(function):
    def wrap(request, *args, **kwargs):
        if not request.user.groups.filter(name='School').exists():
            return redirect('student_profile_list') 
        return function(request, *args, **kwargs)
    return wrap

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('student_profile_list')  
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Signup successful! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'authentication/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('student_profile_list')  
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('student_profile_list')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@admin_required
def create_student_profile(request):
    if request.method == "POST":
        form = StudentProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_profile_list')
    else:
        form = StudentProfileForm()
    return render(request, 'create_profile.html', {'form': form})

@login_required
def student_profile_list(request):
    profiles = StudentProfile.objects.all()
    return render(request, 'student_profile_list.html', {'profiles': profiles})

@admin_required
def update_student_profile(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('student_profile_list')
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, 'update_profile.html', {'form': form})

@admin_required
def delete_student_profile(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.method == "POST":
        profile.delete()
        return redirect('student_profile_list')
    return render(request, 'delete_profile.html', {'profile': profile})

@admin_required
def log_volunteer_hours(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == "POST":
        form = VolunteerLogForm(request.POST)
        if form.is_valid():
            volunteer_log = form.save(commit=False)
            volunteer_log.student = student
            volunteer_log.save()
            
            student.hours_completed += volunteer_log.hours_worked
            student.save()
            return redirect('student_profile_list')
    else:
        form = VolunteerLogForm()
    return render(request, 'log_volunteer_hours.html', {'form': form, 'student': student})


@admin_required
def student_attendance(request):
    date_str = request.GET.get('date') or timezone.now().strftime('%Y-%m-%d')
    try:
        selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()

    students = StudentProfile.objects.all()
    student_logs = []

    for student in students:
        log, created = VolunteerLog.objects.get_or_create(student=student, date=selected_date)
        student_logs.append({'student': student, 'log': log})
        print(students, log)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Check for AJAX request
        return render(request, 'attendance/attendance_partial.html', {
            'students': student_logs,
            'selected_date': selected_date,
        })
    else:  # Full page load
        return render(request, 'attendance/attendance.html', {
            'students': student_logs,
            'selected_date': selected_date,
        })


@admin_required
def update_attendance(request, student_id, date):
    student = get_object_or_404(StudentProfile, id=student_id)
    today = timezone.now().date()
   
    log, created = VolunteerLog.objects.get_or_create(student=student, date=date)

    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        hours_worked = request.POST.get('hours_worked')

        if start_time and end_time:
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()
            log.start_time = start_time
            log.end_time = end_time

        log.status = status
        log.notes = notes

        if hours_worked:
            log.hours_worked = float(hours_worked)

        log.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})

def student_details(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    volunteer_logs = VolunteerLog.objects.filter(student=student)
    
    total_hours = 0
    for log in volunteer_logs:
        if log.status == 'Present':
            if log.hours_worked is None:
                total_hours += 7
            else:
                total_hours += log.hours_worked
    
    return render(request, 'student_details.html', {
        'student': student,
        'volunteer_logs': volunteer_logs,
        'total_hours': total_hours
    })

def student_logs(request):
    students = StudentProfile.objects.all()
    
    student_data = []
    
    for student in students:
        volunteer_logs = VolunteerLog.objects.filter(student=student)
        total_hours = 0
        for log in volunteer_logs:
            print(log)
            if log.status == 'Present':
                if log.hours_worked is None:
                    total_hours += 7
                else:
                    total_hours += log.hours_worked
        student_data.append({
            'student': student,
            'volunteer_logs': volunteer_logs,
            'total_hours': total_hours
        })
    
    return render(request, 'student_logs.html', {'student_data': student_data})


def get_start_of_week(date):
    """Get the start of the week (Monday)."""
    start = date - timedelta(days=date.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0)

def get_end_of_week(date):
    """Get the end of the week (Sunday)."""
    end = date + timedelta(days=(6 - date.weekday()))
    return end.replace(hour=23, minute=59, second=59, microsecond=0)
import decimal

def calendar_student_logs(request):
    # Get the current date or the date passed from the frontend
    current_date = timezone.now()
    week_start_date = get_start_of_week(current_date)
    week_end_date = get_end_of_week(current_date)

    # Get student data and their logs for the week
    students = StudentProfile.objects.all()
    student_data = []

    for student in students:
        volunteer_logs = VolunteerLog.objects.filter(student=student, date__range=[week_start_date, week_end_date])
        total_hours = 0
        formatted_logs = []

        for log in volunteer_logs:
            if log.status == 'Present':
                if log.hours_worked is None:
                    total_hours += 7
                else:
                    total_hours += log.hours_worked

                formatted_logs.append({
                    'date': log.date.isoformat(),
                    'start_time': log.start_time.strftime('%H:%M') if log.start_time else None,
                    'end_time': log.end_time.strftime('%H:%M') if log.end_time else None,
                    'hours_worked': float(log.hours_worked) if isinstance(log.hours_worked, decimal.Decimal) else log.hours_worked,
                    'notes': log.notes or '',
                })

        # Ensure total_hours is converted to float if it's a Decimal
        student_data.append({
            'id': student.id,
            'name': f"{student.first_name} {student.last_name}",
            'logs': formatted_logs,
            'total_hours': float(total_hours) if isinstance(total_hours, decimal.Decimal) else total_hours
        })

    # Convert to JSON
    student_data_json = json.dumps(student_data)

    # Pass the dynamic data to the template
    return render(request, 'calendar.html', {
        'student_data': student_data_json,
        'week_start_date': week_start_date,
        'week_end_date': week_end_date
    })