from django.shortcuts import redirect, get_object_or_404
import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import ScheduleEntry, StudentGrade
from .models import TeacherProfile
from .models import Subject
from .models import SubjectGrade
from .models import Classroom
from .models import StudentProfile
from .models import Grade
from .models import Absence
from .models import Exams
from datetime import datetime, timedelta
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
    student = request.user.studentprofile
    classroom = student.classroom

    # ===== DATE AND TIME INFO =====
    now = datetime.now()
    current_date = now.strftime("%B %d, %Y")
    current_time = now.strftime("%H:%M")
    current_day = now.strftime("%A")

    # ===== TODAY'S CLASSES =====
    todays_classes = []
    classes_today = 0

    if classroom:
        todays_classes = ScheduleEntry.objects.filter(
            classroom=classroom,
            day_of_week=current_day
        ).select_related('subject', 'teacher').order_by('start_time')
        classes_today = todays_classes.count()

    # ===== UPCOMING EXAMS (NEXT 7 DAYS) =====
    upcoming_exams_count = 0
    if classroom:
        upcoming_exams = Exams.objects.filter(
            classroom=classroom,
            date__gte=now.date(),
            date__lte=now.date() + timedelta(days=7)
        )
        upcoming_exams_count = upcoming_exams.count()

    # ===== STUDENT GRADES =====
    student_grades = StudentGrade.objects.filter(
        student=student
    ).select_related('grade')

    # Calculate overall average
    all_grades = [sg.grade.grade for sg in student_grades]
    average_grade = sum(all_grades) / len(all_grades) if all_grades else 0

    # ===== CALCULATE CLASS RANK =====
    student_rank = 1
    total_students = 1

    if classroom:
        students_in_class = StudentProfile.objects.filter(classroom=classroom)
        student_averages = []

        for s in students_in_class:
            s_grades = StudentGrade.objects.filter(
                student=s).select_related('grade')
            if s_grades.exists():
                avg = sum([sg.grade.grade for sg in s_grades]) / \
                    s_grades.count()
                student_averages.append((s, avg))

        # Sort by average (highest first)
        student_averages.sort(key=lambda x: x[1], reverse=True)

        # Find current student's rank
        for rank, (s, avg) in enumerate(student_averages, 1):
            if s.id == student.id:
                student_rank = rank
                break

        total_students = len(student_averages)

    # ===== FIND BEST SUBJECT =====
    subject_averages = {}

    for sg in student_grades:
        try:
            subject_grade = SubjectGrade.objects.get(grade=sg.grade)
            subject = subject_grade.subject

            if subject.id not in subject_averages:
                subject_averages[subject.id] = {
                    'name': subject.name,
                    'grades': []
                }
            subject_averages[subject.id]['grades'].append(sg.grade.grade)
        except SubjectGrade.DoesNotExist:
            continue

    best_subject_name = "N/A"
    best_subject_avg = 0

    for subject_id, data in subject_averages.items():
        avg = sum(data['grades']) / len(data['grades'])
        if avg > best_subject_avg:
            best_subject_avg = avg
            best_subject_name = data['name']

    # ===== THIS WEEK STATISTICS =====
    week_start = now - timedelta(days=now.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday

    # Classes this week (Mon-Fri)
    classes_this_week = 0
    if classroom:
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        classes_this_week = ScheduleEntry.objects.filter(
            classroom=classroom,
            day_of_week__in=weekdays
        ).count()

    # Exams this week
    exams_this_week = 0
    if classroom:
        exams_this_week = Exams.objects.filter(
            classroom=classroom,
            date__gte=week_start.date(),
            date__lte=week_end.date()
        ).count()

    # New grades this week
    grades_this_week = StudentGrade.objects.filter(
        student=student,
        grade__date__gte=week_start.date(),
        grade__date__lte=week_end.date()
    ).count()

    # Attendance this week
    absences_this_week = Absence.objects.filter(
        student=student,
        date__gte=week_start.date(),
        date__lte=week_end.date()
    ).count()

    # Calculate attendance rate for this week
    daily_classes = classes_this_week / 5 if classes_this_week > 0 else 0
    days_passed = (now.date() - week_start.date()).days + 1
    if days_passed > 5:
        days_passed = 5  # Cap at weekdays

    total_classes_so_far = daily_classes * days_passed

    if total_classes_so_far > 0:
        attendance_this_week = int(
            ((total_classes_so_far - absences_this_week) / total_classes_so_far) * 100)
    else:
        attendance_this_week = 100

    # Ensure attendance is between 0 and 100
    attendance_this_week = max(0, min(100, attendance_this_week))

    # ===== ANNOUNCEMENTS  =====
    announcements = [
        {
            'title': 'Parent-Teacher Meeting',
            'message': 'Scheduled for next week. Check your email for details.',
            'date': now + timedelta(days=7)
        },
        {
            'title': 'Important Notice',
            'message': 'Remember to submit all pending assignments.',
            'date': now
        }
    ]

    # ===== PREPARE CONTEXT =====
    context = {
        'student': student,
        'current_date': current_date,
        'current_time': current_time,
        'current_day': current_day,

        # Today's info
        'classes_today': classes_today,
        'todays_classes': todays_classes,

        # Cards info
        'upcoming_exams_count': upcoming_exams_count,
        'student_rank': student_rank,
        'total_students': total_students,
        'best_subject_name': best_subject_name,
        'best_subject_avg': best_subject_avg,
        'average_grade': average_grade,

        # This week stats
        'classes_this_week': classes_this_week,
        'exams_this_week': exams_this_week,
        'grades_this_week': grades_this_week,
        'attendance_this_week': attendance_this_week,

        # Announcements
        'announcements': announcements,
    }

    return render(request, 'student_main.html', context)


@login_required
@student_required
def student_time_table(request):
    student = request.user.studentprofile
    classroom = student.classroom

    if not classroom:
        messages.error(request, "You are not assigned to a classroom.")
        return render(request, 'student_timeTable.html', {
            'days': [],
            'time_slots': [],
            'timetable_data': []
        })

    # Get all schedule entries for this classroom
    schedule = ScheduleEntry.objects.filter(
        classroom=classroom
    ).select_related('subject', 'teacher')

    # Define days
    days = ["Luni", "Marti", "Miercuri", "Joi", "Vineri"]

    # Get unique time slots
    time_slots = sorted(set(entry.start_time for entry in schedule))

    print(f"Time slots found: {[str(t) for t in time_slots]}")

    # Map subject names to CSS classes
    subject_color_map = {
        'matematica': 'subject-math',
        'engleza': 'subject-english',
        'romana': 'subject-romana',
        'stiinte': 'subject-science',
        'istorie': 'subject-history',
        'fizica': 'subject-physics',
        'chimie': 'subject-chemistry',
        'biologie': 'subject-biology',
        'educatie fizica': 'subject-pe',
        'informatica': 'subject-informatica',
    }

    # Build the timetable data
    timetable_data = []

    for time_slot in time_slots:
        # Format time for display
        start_hour = time_slot.hour
        end_hour = start_hour + 1
        time_display = f"{start_hour:02d}:00 - {end_hour:02d}:00"

        row = {
            'time': time_display,
            'cells': []
        }

        for day in days:
            # Finding entry for this specific time and day
            entry = schedule.filter(
                start_time=time_slot,
                day_of_week=day
            ).first()

            if entry:
                subject_lower = entry.subject.name.lower()
                css_class = subject_color_map.get(
                    subject_lower, 'subject-default')

                cell_data = {
                    'subject': entry.subject.name,
                    'teacher': f"{entry.teacher.user.first_name} {entry.teacher.user.last_name}",
                    'css_class': css_class,
                    'empty': False
                }

            else:
                cell_data = {
                    'subject': '-',
                    'teacher': '',
                    'css_class': 'subject-empty',
                    'empty': True
                }
                print(f"{time_display} {day}: Empty")

            row['cells'].append(cell_data)

        timetable_data.append(row)

    context = {
        'student': student,
        'days': days,
        'timetable_data': timetable_data,
        'numestudent': student.user.first_name
    }

    return render(request, 'student_timeTable.html', context)


@login_required
@student_required
def student_calendar(request):
    student = request.user.studentprofile
    exams = Exams.objects.all()
    dict_exams = [
        {'id': e.id,
         'type': e.type,
         'date': e.date.isoformat(),
         'teacher': f"{e.teacher.user.first_name} {e.teacher.user.last_name}",
         'subject': e.subject.name} for e in exams
    ]

    print(dict_exams)

    context = {
        'exams': json.dumps(dict_exams),
        'numestudent': student.user.first_name
    }

    return render(request, 'student_calendar.html', context)


@login_required
@student_required
def student_attendance(request):
    student = request.user.studentprofile

    absente = Absence.objects.filter(
        student=student
    )

    absente_dict = [{
        'note': a.note,
        'date': a.date.isoformat(),
        'name': f"{a.subject.name}",
        'teacher': f"{a.recorded_by.user.first_name} {a.recorded_by.user.last_name}"}
        for a in absente
    ]

    context = {
        'total_absences': 100,
        'monthly_absences': 7,
        'most_missed_subject': "romana",
        'absences': absente_dict
    }
    return render(request, 'student_attendance.html', context)


@login_required
@student_required
def student_grades(request):
    try:
        student = request.user.studentprofile

        # Get all grades for this student
        student_grades = StudentGrade.objects.filter(
            student=student
        ).select_related('grade')

        student_classRoom = student.classroom

        # Organize grades by subject
        subjects_dict = {}

        student_subjects = ScheduleEntry.objects.filter(
            classroom=student_classRoom
        )

        student_subjects = list(student_subjects)

        student_subjects_dicts = [
            {'id': subj.id, 'name': subj.subject.name} for subj in student_subjects
        ]

        for student_grade in student_grades:
            grade_obj = student_grade.grade

            # Get the subject through SubjectGrade
            try:
                subject_grade = SubjectGrade.objects.get(grade=grade_obj)
                subject = subject_grade.subject

                # Initialize subject in dictionary if not exists
                if subject.id not in subjects_dict:
                    subjects_dict[subject.id] = {
                        'id': subject.id,
                        'name': subject.name,
                        'code': f'SUB{subject.id}',
                        'teacher': 'N/A',  # We'll add this next
                        'grades': []
                    }

                # Add grade to the subject
                subjects_dict[subject_grade.subject.id]['grades'].append(
                    grade_obj)

            except SubjectGrade.DoesNotExist:
                # Skip if no subject is linked to this grade
                continue

        for subject_id in subjects_dict.keys():
            grade_dict = [
                {'id': gr.id, 'grade': gr.grade, 'type': gr.evaluation_type, 'date': gr.date} for gr in subjects_dict[subject_id]['grades']
            ]
            subjects_dict[subject_id]['grades'] = grade_dict

        # Get teacher names for each subject
        for subject_id, subject_data in subjects_dict.items():
            try:
                subject = Subject.objects.get(id=subject_id)

                # Get teacher who teaches this subject
                teacher_profile = TeacherProfile.objects.filter(
                    subjects=subject).first()

                if teacher_profile:
                    subject_data['teacher'] = f"{teacher_profile.user.first_name} {teacher_profile.user.last_name}"

                grades_list = subject_data['grades']

                for grade in grades_list:
                    grade['date'] = grade['date'].isoformat()

                subject_data['grades'] = grades_list

            except Subject.DoesNotExist:
                pass

        # Convert dictionary to list
        subjects_list = list(subjects_dict.values())

        print("aici")
        print(subjects_list)

        # Prepare context
        context = {
            'subjects': subjects_list,
            'subjects_json': json.dumps(subjects_list),
            'numestudent': student.user.first_name
        }

        return render(request, 'student_grades.html', context)
    except Exception as e:
        messages.error(request, f"Error loading grades: {str(e)}")
        return render(request, 'student_grades.html', {
            'subjects': [],
            'subjects_json': [],
            'numestudent': student.user.first_name
        })


@login_required
def teacher_main(request):
    try:
        teacher_profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        teacher_profile = None

    classrooms = Classroom.objects.filter(
        scheduleentry__teacher=teacher_profile).distinct()

    return render(request, 'teacher_main.html', {
        'classrooms': classrooms,
    })


@login_required
@teacher_required
def teacher_classroom_detail(request, class_id):
    classroom = Classroom.objects.get(id=class_id)
    teacher = TeacherProfile.objects.get(user=request.user)

    students = StudentProfile.objects.filter(classroom=classroom)
    subjects = teacher.subjects.all()

    catalog = []

    for student in students:

        row = {
            "student": student,
            "subjects": []
        }

        for subject in subjects:

            grades = (
                Grade.objects
                .filter(studentgrade__student=student,
                        subjectgrade__subject=subject)
                .select_related("exam")
            )

            row["subjects"].append({
                "subject": subject,
                "grades": grades
            })

        catalog.append(row)

    absences = Absence.objects.filter(
        student__classroom=classroom
    ).select_related("student", "subject", "recorded_by")

    exams = Exams.objects.filter(
        classroom=classroom,
        subject__in=teacher.subjects.all()
    ).select_related("subject").order_by("-date")

    return render(request, "teacher_classroom.html", {
        "teacher": teacher,
        "classroom": classroom,
        "students": students,
        "subjects": subjects,
        "catalog": catalog,
        "absences": absences,
        "exams": exams,
    })


@login_required
@teacher_required
def add_grade(request, class_id):
    if request.method == "POST":
        teacher = TeacherProfile.objects.get(user=request.user)
        classroom = Classroom.objects.get(id=class_id)

        student_id = request.POST["student"]
        subject_id = request.POST["subject"]
        grade_value = int(request.POST["grade"])
        date_str = request.POST["date"]
        exam_id = request.POST.get("exam")

        student = StudentProfile.objects.get(id=student_id)
        subject = Subject.objects.get(id=subject_id)

        # convert date
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # validare: verificăm că profesorul predă materia
        if subject not in teacher.subjects.all():
            messages.error(request, "Nu predai această materie.")
            return redirect("teacher-classroom", class_id=class_id)

        # dacă a fost selectată o evaluare:
        exam = None
        if exam_id:
            exam = Exams.objects.filter(id=exam_id, teacher=teacher).first()
            if not exam:
                messages.error(request, "Evaluare invalidă.")
                return redirect("teacher-classroom", class_id=class_id)

        grade_obj = Grade.objects.create(
            date=date_obj,
            grade=grade_value,
            exam=exam
        )

        StudentGrade.objects.create(student=student, grade=grade_obj)
        SubjectGrade.objects.create(subject=subject, grade=grade_obj)

        messages.success(request, "Nota a fost adăugată cu succes!")
        return redirect("teacher-classroom", class_id=class_id)

    messages.error(request, "Eroare la adăugarea notei.")
    return redirect("teacher-classroom", class_id=class_id)


@login_required
@teacher_required
def add_absence(request, class_id):
    if request.method == "POST":
        teacher = TeacherProfile.objects.get(user=request.user)
        classroom = Classroom.objects.get(id=class_id)

        student_id = request.POST["student"]
        subject_id = request.POST.get("subject")
        date_str = request.POST["date"]
        time_str = request.POST["time"]
        note = request.POST.get("note", "").strip()

        student = StudentProfile.objects.get(id=student_id)

        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        time_obj = datetime.strptime(time_str, "%H:%M").time()

        weekday = date_obj.weekday()

        if weekday >= 5:
            messages.error(request, "Nu poti adauga absente in weekend.")
            return redirect("teacher-classroom", class_id=class_id)

        subject = None
        if subject_id:
            subject = Subject.objects.get(id=subject_id)

        Absence.objects.create(
            student=student,
            subject=subject,
            date=date_obj,
            time=time_obj,
            recorded_by=teacher,
            note=note
        )

        messages.success(request, "Absenta a fost inregistrata!")
        return redirect("teacher-classroom", class_id=class_id)

    messages.error(request, "Eroare la adaugarea absentei.")
    return redirect("teacher-classroom", class_id=class_id)


@login_required
@teacher_required
def exam_page(request, class_id):
    teacher = TeacherProfile.objects.get(user=request.user)
    classroom = Classroom.objects.get(id=class_id)

    subjects = teacher.subjects.all()

    exams = Exams.objects.filter(
        teacher=teacher,
        classroom=classroom,
        subject__in=subjects
    ).order_by("-date")

    return render(request, "exam_page.html", {
        "teacher": teacher,
        "classroom": classroom,
        "subjects": subjects,
        "exams": exams,
        "exam_types": Exams.EXAM_TYPES,
    })


@login_required
@teacher_required
def add_exam(request, class_id):
    teacher = TeacherProfile.objects.get(user=request.user)
    classroom = Classroom.objects.get(id=class_id)

    if request.method == "POST":
        exam_type = request.POST.get("type")
        subject_id = request.POST.get("subject")
        date_str = request.POST.get("date")
        uploaded = request.FILES.get("file")

        if not exam_type or not subject_id or not date_str:
            messages.error(
                request, "Toate câmpurile sunt obligatorii, în afară de fișier.")
            return redirect("add-exam-page", class_id=class_id)

        subject = Subject.objects.get(id=subject_id)

        if subject not in teacher.subjects.all():
            messages.error(
                request, "Nu poți crea evaluare la o materie pe care nu o predai.")
            return redirect("add-exam-page", class_id=class_id)

        from datetime import datetime
        exam_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        Exams.objects.create(
            type=exam_type,
            date=exam_date,
            classroom=classroom,
            teacher=teacher,
            subject=subject,
            file=uploaded
        )

        messages.success(request, "Evaluarea a fost adăugată cu succes!")
        return redirect("add-exam-page", class_id=class_id)

    return redirect("add-exam-page", class_id=class_id)


@login_required
@teacher_required
def review_page(request):
    return render(request, "review_page.html")
