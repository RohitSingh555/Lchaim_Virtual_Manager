from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_student_profile, name='create_student_profile'),
    path('', views.student_profile_list, name='student_profile_list'),
    path('update/<int:pk>/', views.update_student_profile, name='update_student_profile'),
    path('delete/<int:pk>/', views.delete_student_profile, name='delete_student_profile'),
    path('attendance/', views.student_attendance, name='student_attendance'),
    path('attendance/update/<int:student_id>/', views.update_attendance, name='update_attendance'),
]
