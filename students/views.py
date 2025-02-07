from datetime import date, datetime, time, timedelta
import decimal
import json
import os
import re
import threading
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# Django Imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Case, When, Count, Min, Q, Sum, Value, IntegerField
from django.http import HttpResponse, FileResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.files.storage import default_storage


from io import BytesIO
from openpyxl import Workbook

from .forms import CollegeForm, OrientationDateForm, StudentFileForm, StudentProfileForm, VolunteerLogForm
from .models import College, OrientationDate, Shift, StudentFile, StudentProfile, VolunteerLog


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

def get_shift_availability(user, start_date, shift_type, requested_hours, shift_requested):
    try:
        assigned_shift = Shift.objects.get(type__icontains=shift_type)
    except Shift.DoesNotExist:
        return {"error": f"Shift type '{shift_type}' does not exist."}

    shift_total_time = (
        datetime.combine(date.min, assigned_shift.end_time)
        - datetime.combine(date.min, assigned_shift.start_time)
    ).seconds / 3600

    days_required = (requested_hours // shift_total_time) + (
        1 if requested_hours % shift_total_time != 0 else 0
    )

    current_date = start_date
    working_days = 0
    while working_days < days_required:
        if shift_requested == 'Weekdays' and current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
        if shift_requested == 'Weekends' and current_date.weekday() < 5:
            current_date += timedelta(days=1)
            continue

        if validate_shift_capacity(user, current_date, assigned_shift):
            working_days += 1
        else:
            return {
                "is_available": False,
                "message": f"Capacity exceeded on {current_date.strftime('%Y-%m-%d')} for {shift_type} shift.",
            }

        current_date += timedelta(days=1)

    end_date = current_date - timedelta(days=1)

    return {
        "is_available": True,
        "start_date": start_date,
        "shift_type": shift_type,
        "requested_hours": requested_hours,
        "shift_requested": shift_requested,
        "end_date": end_date,
    }

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt 
def shift_availability_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            shift_type = data['shift_type']
            requested_hours = int(data['requested_hours'])
            shift_requested = data['shift_requested']
            
            availability = get_shift_availability(request.user, start_date, shift_type, requested_hours, shift_requested)
            print(availability)
            return JsonResponse(availability)
        
        except KeyError as e:
            return JsonResponse({"error": f"Missing key: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

def validate_shift_capacity(user, date, assigned_shift):
    """
    Validates if the shift on the given date exceeds its capacity.
    Superusers can always be assigned shifts regardless of capacity.
    """
    if user.is_superuser:
        return True

    shift_students_count = VolunteerLog.objects.filter(date=date, shift=assigned_shift).count()
    return shift_students_count < assigned_shift.max_students


def create_student_profile(request):
    if request.method == "POST":
        profile_form = StudentProfileForm(request.POST, request.FILES)
        if profile_form.is_valid():
            student_profile = profile_form.save()
            print(request.FILES)
            files = request.FILES.getlist('documents')  
            for file in files:
                StudentFile.objects.create(student=student_profile, file=file)
            shift_type = request.POST.get('shift_timing')
            college_request_id = request.POST.get('college')
            college = College.objects.get(id=college_request_id)
            student_profile.school = college.name

            try:
                assigned_shift = Shift.objects.get(type__icontains=shift_type)
                student_profile.assigned_shift = assigned_shift
                student_profile.save()
            except Shift.DoesNotExist:
                messages.error(request, "The specified shift type does not exist.")
                return render(request, 'create_profile.html', {'form': profile_form})

            if student_profile.lchaim_orientation_date and student_profile.hours_requested:
                requested_hours = student_profile.hours_requested
                start_date = student_profile.start_date
                start_time = assigned_shift.start_time
                end_time = assigned_shift.end_time

                shift_total_time = (datetime.combine(date.min, end_time) - datetime.combine(date.min, start_time)).seconds / 3600
                days_required = (requested_hours // shift_total_time) + (1 if requested_hours % shift_total_time != 0 else 0)

                current_date = start_date
                working_days = 0

                while working_days < days_required:
                    if (student_profile.shift_requested == 'Weekdays' and current_date.weekday() < 5) or \
                       (student_profile.shift_requested == 'Weekends' and (current_date.weekday() >= 5 or (current_date.weekday() == 4 and shift_type == 'Night'))):
                        if validate_shift_capacity(request.user, current_date, assigned_shift):
                            working_days += 1
                        else:
                            messages.error(
                                request,
                                f"Capacity exceeded on {current_date.strftime('%Y-%m-%d')} for {shift_type} shift."
                            )
                            return render(request, 'create_profile.html', {'form': profile_form})
                    current_date += timedelta(days=1)

                end_date = current_date - timedelta(days=1)
                student_profile.end_date = end_date
                student_profile.save()

                current_date = start_date
                weekdays_selected_str = request.POST.get('weekdays_selected')  # Get as string
                try:
                    weekdays_selected_dict = json.loads(weekdays_selected_str)  # Convert JSON string to dictionary
                    weekdays_selected = list(weekdays_selected_dict.values())  # Extract weekday numbers
                except json.JSONDecodeError:
                    messages.error(request, "Invalid weekdays_selected format.")
                    return render(request, 'create_profile.html', {'form': profile_form})
                while current_date <= end_date:
                    if (student_profile.shift_requested == 'Weekdays' and current_date.weekday() < 5) or \
                       (student_profile.shift_requested == 'Weekends' and (current_date.weekday() >= 5 or (current_date.weekday() == 4 and shift_type == 'Night'))):
                        if current_date.weekday() in weekdays_selected:
                            if validate_shift_capacity(request.user, current_date, assigned_shift):
                                if shift_type == 'Night' and current_date.weekday() in [4, 5, 6]: 
                                    next_date = current_date + timedelta(days=1)
                                    VolunteerLog.objects.create(
                                        student=student_profile,
                                        date=current_date,
                                        shift=assigned_shift,
                                        start_time=time(19, 0),
                                        end_time=time(23, 59),
                                        hours_worked=5,
                                        status='Present'
                                    )
                                    VolunteerLog.objects.create(
                                        student=student_profile,
                                        date=next_date,
                                        shift=assigned_shift,
                                        start_time=time(0, 0),
                                        end_time=time(7, 0),
                                        hours_worked=7,
                                        status='Present'
                                    )
                                else:
                                    VolunteerLog.objects.create(
                                        student=student_profile,
                                        date=current_date,
                                        shift=assigned_shift,
                                        start_time=start_time,
                                        end_time=end_time,
                                        hours_worked=shift_total_time,
                                        status='Present'
                                    )
                            else:
                                messages.error(
                                    request,
                                    f"Capacity exceeded on {current_date.strftime('%Y-%m-%d')} for {shift_type} shift."
                                )
                                return render(request, 'create_profile.html', {'form': profile_form})
                    current_date += timedelta(days=1)

            threading.Thread(target=send_student_creation_email, args=(student_profile,)).start()

            messages.success(request, "Student profile created successfully, and volunteer logs have been generated!")
            return redirect('student_profile_list')
        else:
            messages.error(request, "There were errors in the form. Please correct them.")
    else:
        profile_form = StudentProfileForm()

    return render(request, 'create_profile.html', {'form': profile_form})

@csrf_exempt  
def send_email(request):
    if request.method == 'POST':
        student_email = request.POST.get('email')
        
        if not student_email:
            return JsonResponse({'status': 'error', 'message': 'Student email is missing'})
        
        try:
            # Use get() to retrieve a single student object based on the email
            student = StudentProfile.objects.get(email=student_email)
            
            # You can print the student directly
            print(student)  # This will print the StudentProfile object (e.g., StudentProfile object (54))

            # Pass the actual student object to the threading function
            threading.Thread(target=send_student_creation_email, args=(student,)).start()
            
            return JsonResponse({'status': 'success'})
        
        except StudentProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Student not found'})
        except Exception as e:
            # Log or print the error for debugging
            print(f"Error: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method. Only POST is allowed.'})
                         
def send_student_creation_email(student):
    print(student)
    subject_q = 'New Student Profile Created'
    message = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                padding: 20px;
            }}
            h3 {{
                color: #2c3e50;
            }}
            p {{
                font-size: 16px;
                line-height: 1.6;
            }}
            ul {{
                list-style-type: none;
                padding-left: 0;
            }}
            li {{
                margin-bottom: 8px;
            }}
            b {{
                color: #2980b9;
            }}
            .email-container {{
                background-color: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <p>Dear {student.first_name},</p>
            <p>Welcome to L'chaim! Before you begin your placement, you must be aware of the most 
            important policies at L'chaim. Please read the attached training documents and confirm that you 
            have read and understood them.
            Wishing you the best learning experience and good luck!</p>
            <p>Kind regards,</p>
            <p>Judy</p>
        </div>
    </body>
    </html>
    """

    volunteer_logs = VolunteerLog.objects.filter(student=student)
    wb = Workbook()
    ws = wb.active
    ws.title = f"Schedule for {student.first_name} {student.last_name}"

    headers = ['Date', 'Start Time', 'End Time', 'Shift']
    ws.append(headers)

    for log in volunteer_logs:
        start_time = log.start_time.strftime('%H:%M') if log.start_time else 'N/A'
        end_time = log.end_time.strftime('%H:%M') if log.end_time else 'N/A'
        shift_type = log.shift.type if log.shift and log.shift.type else 'N/A'
        
        # Append the log details to the Excel sheet
        ws.append([log.date, start_time, end_time, shift_type])

    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    excel_filename = f"{student.first_name}_{student.last_name}_schedule.xlsx"

    email = EmailMessage(
        subject=subject_q,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[student.email],  
    )
    email.content_subtype = "html"

    email.attach(excel_filename, excel_file.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    attachments_folder = os.path.join(settings.BASE_DIR, 'attachments')
    if os.path.exists(attachments_folder):
        for file_name in os.listdir(attachments_folder):
            if file_name.endswith('.pdf'):
                file_path = os.path.join(attachments_folder, file_name)
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as file:
                        email.attach(file_name, file.read(), 'application/pdf')
                else:
                    print(f"File {file_name} not found in attachments folder.")
    else:
        print(f"Attachments folder not found at {attachments_folder}.")
    email.send()



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

    is_school_group = request.user.groups.filter(name='School').exists()

    return render(request, 'student_profile_list.html', {
        'page_obj': page_obj,
        'query': query,
        'orientation_date': orientation_date,
        'is_school_group': is_school_group, 
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
        print("Form data:", request.POST)  
        print("File data:", request.FILES)  

        form = StudentProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            student_profile = form.save()

            if 'documents' in request.FILES:
                files = request.FILES.getlist('documents') 
                for file in files:
                    StudentFile.objects.create(student=student_profile, file=file)

            return redirect('student_profile_list')
        else :
            print("File Error:", form.errors)  

    else:
        form = StudentProfileForm(instance=profile)

    existing_files = StudentFile.objects.filter(student=profile)

    return render(request, 'update_profile.html', {
        'form': form,
        'existing_files': existing_files
    })


@admin_required
def delete_student_profile(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.method == "POST":
        profile.delete()
    return redirect('student_profile_list')

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
        hours_worked = log.hours_worked 
        if hours_worked is not None:
            hours = int(hours_worked) 
            minutes = round((hours_worked - hours) * 60) 

            log.hours_worked = f"{hours}:{minutes:02}" 
        else:
            log.hours_worked = "00:00" 

        student_logs.append({'student': student, 'log': log})

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
        return render(request, 'attendance/attendance_partial.html', {
            'students': student_logs,
            'selected_date': selected_date,
        })
    else: 
        return render(request, 'attendance/attendance.html', {
            'students': student_logs,
            'selected_date': selected_date,
        })

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
        print(hours_worked)

        if hours_worked:
            if isinstance(hours_worked, str) and ':' in hours_worked:
                hours, minutes = map(int, hours_worked.split(':'))
                total_hours = hours + minutes / 60.0  
                log.hours_worked = total_hours
            else:
                log.hours_worked = float(hours_worked)
        
        log.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

from django.shortcuts import render, get_object_or_404, redirect
from .models import StudentProfile, VolunteerLog
from datetime import timedelta
import re

def student_details(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    
    # Order logs by date in ascending order (oldest first)
    volunteer_logs = VolunteerLog.objects.filter(student=student).order_by('date')  # Ascending order
    student_files = StudentFile.objects.filter(student=student)
    
    filename_pattern = re.compile(r'([^/]+)$')
    
    # Process the file names using regex
    for file in student_files:
        match = filename_pattern.search(file.file.name)
        if match:
            print(match.group(0))
            file.file = match.group(0)  
    
    total_hours = 0
    for log in volunteer_logs:
        if log.status == 'Present':
            total_hours += log.hours_worked if log.hours_worked else 7
    
    if request.method == 'POST':
        log_id = request.POST.get('log_id')
        action = request.POST.get('action')
        
        # Handle toggle action to mark log as absent
        if action == 'toggle':
            log = get_object_or_404(VolunteerLog, id=log_id, student=student)
            previous_log_data = {
                'start_time': log.start_time,
                'end_time': log.end_time,
                'hours_worked': log.hours_worked,
                'notes': log.notes
            }
            
            log.status = 'Absent'
            log.hours_worked = 0
            log.start_time = None
            log.end_time = None
            log.notes = "Marked as Absent"
            log.save()
            
            last_log = VolunteerLog.objects.filter(student=student).order_by('-date').first()
            if last_log:
                new_date = last_log.date + timedelta(days=1)  # Set the date as the last date + 1
                
                # Create a new log entry with the new date and copy data from the previous log
                new_log = VolunteerLog.objects.create(
                    student=student,
                    date=new_date,
                    status='Present',
                    start_time=previous_log_data['start_time'],
                    end_time=previous_log_data['end_time'],
                    hours_worked=previous_log_data['hours_worked'],
                    notes=previous_log_data['notes']
                )

            return redirect('student_details', student_id=student.id)

        # Handle delete action
        if action == 'delete':
            log = get_object_or_404(VolunteerLog, id=log_id, student=student)
            log.delete()
            return redirect('student_details', student_id=student.id)
    
    return render(request, 'student_details.html', {
        'student': student,
        'volunteer_logs': volunteer_logs,
        'total_hours': total_hours,
        'student_files': student_files
    })


from django.utils.timezone import now
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
        'first_name'  
    )

    student_data = []
    for student in students:
        today = now().date()
        volunteer_logs = VolunteerLog.objects.filter(student=student, date__lte=today).order_by('date')

        total_hours = 0
        latest_date = None

        for log in volunteer_logs:
            if log.status == 'Present':
                total_hours += log.hours_worked if log.hours_worked else 8
            latest_date = log.date if not latest_date or log.date > latest_date else latest_date
        
        total_hours = max(0, total_hours) 
        
        student.hours_completed = total_hours
        student.save()

        hours_requested = student.hours_requested if hasattr(student, 'hours_requested') else 0
        remaining_hours = hours_requested - total_hours

        progress_width = (total_hours / hours_requested) * 100 if hours_requested > 0 else 0
        progress_width = round(progress_width, 2)  

        if student.status == 'Graduated':
            wfstatus = 'Inactive'  
        else:
            wfstatus = 'Active'  

        student_data.append({
            'student': student,
            'volunteer_logs': volunteer_logs,
            'total_hours': total_hours,
            'hours_requested': student.hours_requested,
            'remaining_hours': remaining_hours,
            'progress_width': progress_width,
            'latest_date': latest_date,
            'status': wfstatus  
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
                    'status': log.status,
                    'start_time': log.start_time.strftime('%H:%M') if log.start_time else None,
                    'end_time': log.end_time.strftime('%H:%M') if log.end_time else None,
                    'hours_worked': float(log.hours_worked) if isinstance(log.hours_worked, decimal.Decimal) else log.hours_worked,
                    'notes': log.notes or '',
                })

        student_data.append({
            'id': student.id,
            'phone': student.phone,
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



def download_excel_user_wise(request, id):
    student_data = []
    students = StudentProfile.objects.filter(id=id)
    
    for student in students:
        total_hours = 0  
        
        volunteer_logs = VolunteerLog.objects.filter(student=student, status='Present')
        
        for log in volunteer_logs:
            total_hours += log.hours_worked if log.hours_worked else 7

        hours_requested = student.hours_requested if hasattr(student, 'hours_requested') else 0
        remaining_hours = hours_requested - total_hours
        
        for log in volunteer_logs:
            student_data.append({
                'Student Name': f"{student.first_name} {student.last_name}",
                'Email': student.email,
                'Phone': student.phone,
                'School': student.school,
                'Date of Attendance': log.date,
                'Start Time': log.start_time,
                'End Time': log.end_time,
                'Attendance': log.status,
                'Notes': log.notes if log.notes else 'N/A',
                'Completed Hours': log.hours_worked if log.hours_worked is not None else 'N/A',
                'Remaining Hours': remaining_hours,
                'Status': student.status,
            })

    if not student_data:
        return HttpResponse("No attendance data found for the selected student.", status=404)

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    headers = ['Student Name', 'Email', 'Phone', 'School', 'Date of Attendance', 'Start Time', 'End Time', 'Attendance', 'Notes', 'Completed Hours', 'Remaining Hours', 'Status']
    ws.append(headers)

    for entry in student_data:
        ws.append([
            entry['Student Name'],
            entry['Email'],
            entry['Phone'],
            entry['School'],
            entry['Date of Attendance'],
            entry['Start Time'],
            entry['End Time'],
            entry['Attendance'],
            entry['Notes'],
            entry['Completed Hours'],
            entry['Remaining Hours'],
            entry['Status'],
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={student.first_name}_{student.last_name}_report.xlsx'

    wb.save(response)
    return response

@admin_required
def create_college(request):
    if request.method == 'POST':
        form = CollegeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_profile_list')  
    else:
        form = CollegeForm()

    return render(request, 'create_college.html', {'form': form})

@admin_required
def student_file_details(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    file_logs = StudentFile.objects.filter(student=student)  
    
    return render(request, 'studentfile.html', {
        'student': student,
        'file_logs': file_logs,  
    })

def download_file(request, file_id):
    try:
        file_log = StudentFile.objects.get(id=file_id)
        file_path = file_log.file.path 

        response = FileResponse(open(file_path, 'rb'), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{file_log.file.name}"'
        return response
    except StudentFile.DoesNotExist:
        raise Http404("File not found.")


def remove_file(request, pk):
    student_file = get_object_or_404(StudentFile, pk=pk)
    student_file.delete()
    return redirect('update_student_profile', pk=student_file.student.pk)

class MarkGraduateAPIView(APIView):
    def patch(self, request, pk):
        student = get_object_or_404(StudentProfile, pk=pk)

        if student.status == 'Graduated':
            return Response({"detail": "Student is already graduated."}, status=status.HTTP_400_BAD_REQUEST)

        student.status = 'Graduated'
        student.save()

        return Response({
            "detail": f"Student {student.first_name} {student.last_name} has been marked as graduated.",
            "id": student.id,
            "status": student.status
        }, status=status.HTTP_200_OK)
    
def orientation_date_list(request):
    dates = OrientationDate.objects.all()
    return render(request, 'orientation_date_list.html', {'dates': dates})

# Add a new orientation date
def add_orientation_date(request):
    if request.method == 'POST':
        form = OrientationDateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('orientation_date_list')
    else:
        form = OrientationDateForm()
    return render(request, 'add_orientation_date.html', {'form': form})

# Edit an existing orientation date
def edit_orientation_date(request, pk):
    orientation_date = get_object_or_404(OrientationDate, pk=pk)
    if request.method == 'POST':
        form = OrientationDateForm(request.POST, instance=orientation_date)
        if form.is_valid():
            form.save()
            return redirect('orientation_date_list')
    else:
        form = OrientationDateForm(instance=orientation_date)
    return render(request, 'edit_orientation_date.html', {'form': form})

# Delete an orientation date
def delete_orientation_date(request, pk):
    orientation_date = get_object_or_404(OrientationDate, pk=pk)
    if request.method == 'POST':
        orientation_date.delete()
        return redirect('orientation_date_list')
    return HttpResponse(status=405)  # Method not allowed

def delete_log(request, log_id):
    log = get_object_or_404(VolunteerLog, id=log_id)
    
    # Delete the log
    log.delete()
    
    # Optionally, add a success message
    messages.success(request, "Volunteer log has been deleted successfully.")
    
    # Redirect back to the student's details page or wherever necessary
    return redirect('student_details', student_id=log.student.id)