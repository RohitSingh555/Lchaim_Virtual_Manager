from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from .models import StudentProfile, VolunteerLog
from django.http import JsonResponse
from .forms import StudentProfileForm, VolunteerLogForm

def create_student_profile(request):
    if request.method == "POST":
        form = StudentProfileForm(request.POST)
        if form.is_valid():
            student_profile = form.save()
            return redirect('student_profile_list')  
    else:
        form = StudentProfileForm()

    return render(request, 'create_profile.html', {'form': form})

def student_profile_list(request):
    profiles = StudentProfile.objects.all()
    return render(request, 'student_profile_list.html', {'profiles': profiles})

def update_student_profile(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            student_profile = form.save()
            return redirect('student_profile_list')  
    else:
        form = StudentProfileForm(instance=profile)

    return render(request, 'update_profile.html', {'form': form})

def delete_student_profile(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.method == "POST":
        profile.delete()
        return redirect('student_profile_list')  
    return render(request, 'delete_profile.html', {'profile': profile})

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

            return redirect('student_profile_list')  # Redirect after saving the log
    else:
        form = VolunteerLogForm()

    return render(request, 'log_volunteer_hours.html', {'form': form, 'student': student})

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

        # Convert the start and end times to datetime objects
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