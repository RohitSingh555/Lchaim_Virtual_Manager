# from django.shortcuts import render
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
    # from .models import StudentProfile
# from .serializers import StudentProfileSerializer
#
# class StudentProfileCreateView(APIView):
#     def post(self, request, *args, **kwargs):
#         serializer = StudentProfileSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "Student profile created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
#         return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from .models import StudentProfile
from .forms import StudentProfileForm


def create_student_profile(request):
    if request.method == "POST":
        form = StudentProfileForm(request.POST)
        print(form)
        if form.is_valid():
            print(form.cleaned_data)
            form.save()
            return redirect('student_profile_list')  # Make sure 'student_profile_list' is a valid URL name
    else:
        form = StudentProfileForm()

    return render(request, 'create_profile.html', {'form': form})

def student_profile_list(request):
    profiles = StudentProfile.objects.all()
    print(profiles)
    return render(request, 'student_profile_list.html', {'profiles': profiles})



def update_student_profile(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('student_profile_list')  # Redirect after update
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, 'update_profile.html', {'form': form})
def delete_student_profile(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.method == "POST":
        profile.delete()
        return redirect('student_profile_list')  # Redirect after deletion
    return render(request, 'delete_profile.html', {'profile': profile})
