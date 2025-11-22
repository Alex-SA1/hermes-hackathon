from django.contrib import admin
from django.contrib.auth.models import User
from .models import *

admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(School)
admin.site.register(Classroom)
admin.site.register(Subject)
admin.site.register(Grade)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
