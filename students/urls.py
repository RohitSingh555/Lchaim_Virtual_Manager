# from django.urls import path
# from .views import StudentProfileCreateView

# urlpatterns = [
#     path('api/student-profile/', StudentProfileCreateView.as_view(), name='student-profile-create'),
# ]
# from django.shortcuts import render
# from django.urls import path
# from .views import create_student_profile

# urlpatterns = [
#     path('create-student-profile/', create_student_profile, name='create-student-profile'),
#     path('', views.student_profile_list, name='student_profile_list'),

#     path('success/', lambda request: render(request, 'success.html'), name='success'),
# ]


from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_student_profile, name='create_student_profile'),
    path('', views.student_profile_list, name='student_profile_list'),
    path('update/<int:pk>/', views.update_student_profile, name='update_student_profile'),
    path('delete/<int:pk>/', views.delete_student_profile, name='delete_student_profile'),
]
