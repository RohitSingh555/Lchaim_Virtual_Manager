from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

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
    path('student/calender/', views.calendar_student_logs, name='calendar_student_logs'),
    path('student/<int:student_id>/logs/', views.student_details, name='student_details'),
    path('download-excel/<str:selected_date>/', views.download_excel, name='download_excel'),
    path('download-excel-user-wise/<str:id>/', views.download_excel_user_wise, name='download_excel_user_wise'),
    path('create_college/', views.create_college, name='create_college'),
]
