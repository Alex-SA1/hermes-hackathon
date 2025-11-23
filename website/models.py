from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


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


class School(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Classroom(models.Model):
    number = models.CharField(max_length=2)
    letter = models.CharField(max_length=1)
    form_teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classes_led",
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    @property
    def name(self):
        return f"{self.number}{self.letter}"

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fathers_initial = models.CharField(max_length=5, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    classroom = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, null=True, blank=True, default=None
    )

    def __str__(self):
        return f"{self.user.first_name} {self.fathers_initial} {self.user.last_name}"


class Exams(models.Model):

    EXAM_TYPES = [
        ("Test", "Test"),
        ("Tema", "Tema"),
        ("Proiect", "Proiect"),
        ("Ascultare", "Ascultare"),
    ]

    type = models.CharField(max_length=10, choices=EXAM_TYPES)
    date = models.DateField()
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    file = models.FileField(
        upload_to="exam_files/",
        null=True,
        blank=True
    )

    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, related_name="exams"
    )

    def __str__(self):
        return f"{self.type} {self.subject.name} - {self.date}"


class Grade(models.Model):
    date = models.DateField()
    evaluation_type = models.CharField(max_length=30)
    grade = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Grade must be at least 1"),
            MaxValueValidator(10, message="Grade cannot be greater than 10"),
        ]
    )

    exam = models.ForeignKey(
        Exams,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grades'
    )

    def __str__(self):
        return f"{self.grade}"


class SubjectGrade(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subject.name}: {self.grade.grade}"


class StudentGrade(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} -> {self.grade.grade}"


class ScheduleEntry(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="schedule",
    )
    day_of_week = models.CharField(max_length=10)
    start_time = models.TimeField()

    def __str__(self):
        return f"{self.classroom.name} - {self.subject.name} ({self.day_of_week} {self.start_time})"


class Absence(models.Model):
    student = models.ForeignKey(
        'StudentProfile',
        on_delete=models.CASCADE,
        related_name='absences'
    )
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    date = models.DateField()
    time = models.TimeField()
    recorded_by = models.ForeignKey(
        'TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Teacher who recorded the absence (optional)"
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-date', 'time']
        verbose_name = "Absence"
        verbose_name_plural = "Absences"

    def __str__(self):
        subj = self.subject.name if self.subject else "—"
        return f"{self.student} — {subj} @ {self.date} {self.time}"
