import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'  # Include all fields available in the User model


class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm

    fieldsets = (
        ('Authentication', {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff')}),
    )

    list_display = ('username', 'first_name', 'last_name',
                    'email', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fathers_initial = models.CharField(max_length=5, blank=True, null=False)
    phone = models.CharField(max_length=20, blank=True, null=False)

    def __str__(self):
        return self.user.first_name + " " + self.fathers_initial + " " + self.user.last_name


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name


class School(models.Model):
    name = models.CharField(max_length=100, blank=True, null=False)


class Classroom(models.Model):
    number = models.CharField(max_length=2, blank=True, null=False)
    letter = models.CharField(max_length=1, blank=True, null=False)
    form_teacher = models.OneToOneField(
        TeacherProfile, on_delete=models.CASCADE)
    school = models.OneToOneField(School, on_delete=models.CASCADE)


class Subject(models.Model):
    name = models.CharField(max_length=30, blank=True, null=False)
    teacher = models.OneToOneField(TeacherProfile, on_delete=models.CASCADE)


class Grade(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    subject = models.OneToOneField(Subject, on_delete=models.CASCADE)
    date = models.DateField
    evaluation_type = models.CharField(max_length=30, blank=True, null=False)
    grade = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Grade must be at least 1"),
            MaxValueValidator(10, message="Grade cannot be greater than 10")
        ],
        blank=True, null=False)
