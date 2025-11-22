from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from website.decorators import student_required, teacher_required


def home(request):
    return render(request, 'index.html', {})


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if hasattr(user, 'teacherprofile'):
                messages.success(
                    request, "You have been logged in as a Teacher!")

                return redirect('teacher-page')
            elif hasattr(user, 'studentprofile'):
                messages.success(
                    request, "You have been logged in as a Student!")
                return redirect('student-page')

            return redirect('home')
        else:
            messages.error(
                request, "There was an error loggin in, please try again!")

            return redirect('home')
    else:
        return render(request, 'login.html', {})


def logout_user(request):

    logout(request)

    messages.success(request, "You have been logged out!")

    return redirect('home')


@login_required
@student_required
def student_main(request):
    return render(request, 'student_main.html', {})


@login_required
@teacher_required
def teacher_main(request):
    return render(request, 'teacher_main.html', {})
