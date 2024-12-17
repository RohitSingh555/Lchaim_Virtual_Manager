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
    today = timezone.now().date()
    students = StudentProfile.objects.all()
    student_logs = []

    for student in students:
        log, created = VolunteerLog.objects.get_or_create(student=student, date=today)
        student_logs.append({'student': student, 'log': log})

    return render(request, 'attendance/attendance.html', {
        'students': student_logs,
        'today': today,
    })

@admin_required
def update_attendance(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    today = timezone.now().date()
    log, created = VolunteerLog.objects.get_or_create(student=student, date=today)

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