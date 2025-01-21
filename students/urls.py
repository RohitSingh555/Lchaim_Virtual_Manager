from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('create/', views.create_student_profile, name='create_student_profile'),
    path('', views.student_profile_list, name='student_profile_list'),
    path('graduated/', views.student_graduated_list, name='student_graduated_list'),
    path('update/<int:pk>/', views.update_student_profile, name='update_student_profile'),
    path('delete/<int:pk>/', views.delete_student_profile, name='delete_student_profile'),
    path('attendance/', views.student_attendance, name='student_attendance'),
    path('attendance/update/<int:student_id>/<str:date>/', views.update_attendance, name='update_attendance'),

    path('auth/signup/', views.signup_view, name='signup_page'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),

    path('student/logs/', views.student_logs, name='student_logs'),
    path('student/calendar/', views.calendar_student_logs, name='calendar_student_logs'),
    path('student/<int:student_id>/logs/', views.student_details, name='student_details'),
    path('download-excel/<str:selected_date>/', views.download_excel, name='download_excel'),
    path('download-excel-user-wise/<str:id>/', views.download_excel_user_wise, name='download_excel_user_wise'),
    path('create_college/', views.create_college, name='create_college'),
    path('students/<int:student_id>/files/', views.student_file_details, name='student_files'),
    path('download/<int:file_id>/', views.download_file, name='download_file'),
    path('remove-file/<int:pk>/', views.remove_file, name='remove_file'), 
    path('send-email/', views.send_email, name='send_email'),

    path('api/shift-availability/', views.shift_availability_api, name='shift_availability_api'),
    path('api/students/<int:pk>/mark-graduate/', views.MarkGraduateAPIView.as_view(), name='mark-graduate'),

    path('orientation-dates/', views.orientation_date_list, name='orientation_date_list'),
    path('orientation-dates/add/', views.add_orientation_date, name='add_orientation_date'),
    path('orientation-dates/edit/<int:pk>/', views.edit_orientation_date, name='edit_orientation_date'),
    path('orientation-dates/delete/<int:pk>/', views.delete_orientation_date, name='delete_orientation_date'),
    path('log/delete/<int:log_id>/', views.delete_log, name='delete_log'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)