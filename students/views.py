from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
import decimal
from openpyxl import Workbook
from django.http import HttpResponse
from .models import StudentProfile, VolunteerLog
from django.db.models import Sum
from django.http import JsonResponse
from .forms import StudentProfileForm, VolunteerLogForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from datetime import timedelta
import json
from django.db.models import Q
from django.core.paginator import Paginator
from decimal import Decimal
from django.db.models import Case, When, Value, IntegerField

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

@admin_required
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

def create_student_profile(request):
    if request.method == "POST":
        print(request.POST)
        form = StudentProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_profile_list')
        else:
            print(form.errors)
    else:
        form = StudentProfileForm()
    return render(request, 'create_profile.html', {'form': form})

@login_required
def student_profile_list(request):
    query = request.GET.get('q', '')
    orientation_date = request.GET.get('orientation_date', '')

    profiles = StudentProfile.objects.all()

    if query:
        profiles = profiles.filter(
            first_name__icontains=query
        ) | profiles.filter(
            last_name__icontains=query
        ) | profiles.filter(
            email__icontains=query
        )

    if orientation_date:
        profiles = profiles.filter(lchaim_orientation_date=orientation_date)

    paginator = Paginator(profiles, 10) 
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Check if the user is part of the 'School' group
    is_school_group = request.user.groups.filter(name='School').exists()

    return render(request, 'student_profile_list.html', {
        'page_obj': page_obj,
        'query': query,
        'orientation_date': orientation_date,
        'is_school_group': is_school_group,  # Pass the boolean flag
    })

@login_required
def student_graduated_list(request):
    query = request.GET.get('q', '')
    orientation_date = request.GET.get('orientation_date', '')

    profiles = StudentProfile.objects.filter(status='Graduated')


    if query:
        profiles = profiles.filter(
            first_name__icontains=query
        ) | profiles.filter(
            last_name__icontains=query
        ) | profiles.filter(
            email__icontains=query
        )

    if orientation_date:
        profiles = profiles.filter(lchaim_orientation_date=orientation_date)

    paginator = Paginator(profiles, 10) 
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

  
    is_school_group = request.user.groups.filter(name='School').exists()

    return render(request, 'graduated.html', {
        'page_obj': page_obj,
        'query': query,
        'orientation_date': orientation_date,
        'is_school_group': is_school_group,  
    })



@admin_required
def update_student_profile(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.method == "POST":
        print(request.POST)
        form = StudentProfileForm(request.POST, instance=profile)
        

        if form.is_valid():
            print(request.POST)
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

    students = StudentProfile.objects.filter(status='Training')
    student_logs = []

    for student in students:
        log, created = VolunteerLog.objects.get_or_create(student=student, date=selected_date)
        student_logs.append({'student': student, 'log': log})
        print(students, log)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
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
    print(date)
    log, created = VolunteerLog.objects.get_or_create(student=student, date=date)
    print(log)
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

@admin_required
def student_details(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    volunteer_logs = VolunteerLog.objects.filter(student=student)
    
    total_hours = 0
    for log in volunteer_logs:
        if log.status == 'Present':
            if log.status == 'Present':
                total_hours += log.hours_worked if log.hours_worked else 7
    
    return render(request, 'student_details.html', {
        'student': student,
        'volunteer_logs': volunteer_logs,
        'total_hours': total_hours
    })

@admin_required
def student_logs(request):
    query = request.GET.get('q', '').strip()
    
    if query:
        students = StudentProfile.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )
    else:
        students = StudentProfile.objects.all()

    students = students.order_by(
        Case(
            When(status='Training', then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        ),
        'first_name'  # You can add secondary ordering if needed, e.g., by first name
    )

    student_data = []
    for student in students:
        volunteer_logs = VolunteerLog.objects.filter(student=student)
        total_hours = 0
        for log in volunteer_logs:
            if log.status == 'Present':
                total_hours += log.hours_worked if log.hours_worked else 7
        

        student.hours_completed = total_hours
        student.save()
        
        hours_requested = student.hours_requested if hasattr(student, 'hours_requested') else 0
        remaining_hours = hours_requested - total_hours

        progress_width = (total_hours / hours_requested) * 100 if hours_requested > 0 else 0

        # Optionally, round the value
        progress_width = round(progress_width, 2) 
        if total_hours >= hours_requested:
            student.status = 'Graduated'
            student.save()

        if student.status == 'Graduated':
            wfstatus = 'Inactive'  # If graduated, the wfstatus becomes Active
        else:
            wfstatus = 'Active' 

        student.save()

        student_data.append({
            'student': student,
            'volunteer_logs': volunteer_logs,
            'total_hours': total_hours,
            'hours_requested': student.hours_requested,
            'remaining_hours': remaining_hours,
            'progress_width': progress_width,
            'status' : wfstatus  
        })

    return render(request, 'student_logs.html', {'student_data': student_data, 'query': query})



def get_start_of_week(date):
    """Get the start of the week (Monday)."""
    start = date - timedelta(days=date.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0)

def get_end_of_week(date):
    """Get the end of the week (Sunday)."""
    end = date + timedelta(days=(6 - date.weekday()))
    return end.replace(hour=23, minute=59, second=59, microsecond=0)

@admin_required
def calendar_student_logs(request):
    current_date = timezone.now()
    week_start_date = get_start_of_week(current_date)
    week_end_date = get_end_of_week(current_date)

    students = StudentProfile.objects.all()
    student_data = []

    for student in students:
        volunteer_logs = VolunteerLog.objects.filter(student=student)
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

        student_data.append({
            'id': student.id,
            'name': f"{student.first_name} {student.last_name}",
            'logs': formatted_logs,
            'total_hours': float(total_hours) if isinstance(total_hours, decimal.Decimal) else total_hours
        })

    student_data_json = json.dumps(student_data)

    return render(request, 'calendar.html', {
        'student_data': student_data_json,
        'week_start_date': week_start_date,
        'week_end_date': week_end_date
    })

def download_excel(request, selected_date):
    date = datetime.strptime(selected_date, '%Y-%m-%d').date()

    student_data = []

    students = StudentProfile.objects.all()
    for student in students:
        volunteer_logs = VolunteerLog.objects.filter(student=student, date=date)

        for log in volunteer_logs:
            student_data.append({
                'Student Name': f"{student.first_name} {student.last_name}",
                'School': student.school,
                'Date of Attendance': log.date,
                'Hours Worked': log.hours_worked if log.hours_worked is not None else 'N/A',
                'Status': log.status,
                'Notes': log.notes if log.notes else 'N/A',
            })

    if not student_data:
        return HttpResponse("No attendance data found for the selected date.", status=404)

    wb = Workbook()
    ws = wb.active
    ws.title = f"Attendance_{date}"

    headers = ['Student Name', 'School', 'Date of Attendance', 'Hours Worked', 'Status', 'Notes']
    ws.append(headers)

    for entry in student_data:
        ws.append([entry['Student Name'], entry['School'], entry['Date of Attendance'], entry['Hours Worked'], entry['Status'], entry['Notes']])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=attendance_{date}.xlsx'

    wb.save(response)
    return response