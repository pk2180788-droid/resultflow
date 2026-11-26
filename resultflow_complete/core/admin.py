from django.contrib import admin
from .models import Profile,Student,Subject,Exam,Mark,TeacherAssignment
admin.site.register([Profile,Student,Subject,Exam,Mark,TeacherAssignment])
