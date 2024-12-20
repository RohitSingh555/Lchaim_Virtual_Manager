from datetime import datetime
from django.core.mail import EmailMessage
import os
import re
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
import decimal
from openpyxl import Workbook
from django.http import HttpResponse, FileResponse, Http404
from .models import StudentFile, StudentProfile, VolunteerLog
from django.db.models import Sum
from django.http import JsonResponse
from .forms import CollegeForm, StudentFileForm, StudentProfileForm, VolunteerLogForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from datetime import timedelta
import json
from django.db.models import Q
from django.conf import settings
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
        profile_form = StudentProfileForm(request.POST, request.FILES)  # Pass request.FILES to handle uploaded files
        if profile_form.is_valid():
            student_profile = profile_form.save()
            send_student_creation_email(student_profile)
            print(request.FILES)
            files = request.FILES.getlist('documents')  
            for file in files:
                StudentFile.objects.create(student=student_profile, file=file)

            return redirect('student_profile_list') 
    else:
        profile_form = StudentProfileForm()

    return render(request, 'create_profile.html', {'form': profile_form})

def send_student_creation_email(student):
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
            .footer {{
                font-size: 14px;
                color: #808080;
                margin-top: 20px;
            }}
            .footer a {{
                color: #2980b9;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <h3>New Student Profile Created</h3>
            <p>Dear Admin,</p>
            <p>The following student profile has been created:</p>
            <ul>
                <li><b>First Name:</b> {student.first_name}</li>
                <li><b>Last Name:</b> {student.last_name}</li>
                <li><b>Email:</b> {student.email}</li>
                <li><b>Phone:</b> {student.phone}</li>
                <li><b>School:</b> {student.school}</li>
                <li><b>Shift Requested:</b> {student.shift_requested}</li>
                <li><b>Hours Requested:</b> {student.hours_requested}</li>
                <li><b>Comments:</b> {student.comments}</li>
            </ul>
            <p>Warm Regards,<br/>L'chaim Virtual Manager</p>
        </div>
        <div class="footer">
            <p>For any inquiries, please contact <a href="mailto:admin@lchaimretirement.ca">admin@lchaimretirement.ca</a></p>
            <p>&copy; 2024 L'chaim Virtual Manager. All rights reserved.</p>
        </div>
    </body>
    </html>
    """

    email = EmailMessage(
        subject=subject_q,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[student.email],  
    )
    email.content_subtype = "html"  
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

        # Include request.FILES for file handling
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            student_profile = form.save()

            # Handle multiple files
            if 'documents' in request.FILES:
                files = request.FILES.getlist('documents')  # Ensure correct field name
                for file in files:
                    StudentFile.objects.create(student=student_profile, file=file)

            # Redirect to the profile list page
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
        
        # Handle hours worked formatting
        hours_worked = log.hours_worked  # assuming this is a decimal value
        if hours_worked is not None:
            hours = int(hours_worked)  # Integer part is the hours
            minutes = round((hours_worked - hours) * 60)  # Fractional part converted to minutes

            # Format as HH:MM
            log.hours_worked = f"{hours}:{minutes:02}"  # Format minutes as two digits
        else:
            log.hours_worked = "00:00"  # Default if no hours worked

        # Append student and their log
        student_logs.append({'student': student, 'log': log})

    # Print the students and their logs for debugging
    print(student_logs)  # This will show the students and the corresponding logs

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
    
    return render(request, 'student_details.html', {
        'student': student,
        'volunteer_logs': volunteer_logs,
        'total_hours': total_hours,
        'student_files': student_files
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
        'first_name'  
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

        progress_width = round(progress_width, 2) 
        if total_hours >= hours_requested:
            student.status = 'Graduated'
            student.save()

        if student.status == 'Graduated':
            wfstatus = 'Inactive'  
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



def download_excel_user_wise(request, id):
    student_data = []
    students = StudentProfile.objects.filter(id=id)
    
    for student in students:
        total_hours = 0  
        
        # Fetch volunteer logs for the student
        volunteer_logs = VolunteerLog.objects.filter(student=student, status='Present')
        
        for log in volunteer_logs:
            # Add hours worked to the total, or default to 7 if not specified
            total_hours += log.hours_worked if log.hours_worked else 7

        # Calculate remaining hours based on requested hours
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

    # Check if data was found
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