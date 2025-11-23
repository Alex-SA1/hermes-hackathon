
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from website import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('student-page/', views.student_main, name='student-page'),
    path('student-page/grades', views.student_grades, name='student-grades'),
    path('student-page/time_table', views.student_time_table, name='student-table'),
    path('student-page/calendar', views.student_calendar, name='student-calendar'),
    path('student-page/attendance', views.student_attendance,
         name='student-attendance'),

    path('teacher-page/', views.teacher_main, name='teacher-page'),
    path("teacher/classroom/<int:class_id>/",
         views.teacher_classroom_detail, name="teacher-classroom"),
    path("teacher/classroom/<int:class_id>/grade/",
         views.add_grade, name="add-grade"),
    path("teacher/classroom/<int:class_id>/absence/S",
         views.add_absence, name="add-absence"),
    path("teacher/classroom/<int:class_id>/exams/",
         views.exam_page, name="add-exam-page"),
    path("teacher/classroom/<int:class_id>/exams/add/",
         views.add_exam, name="add-exam"),

    path("reviews/", views.review_page, name="reviews-page"),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
