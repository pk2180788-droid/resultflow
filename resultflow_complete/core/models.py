from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES=[('admin','Admin'),('teacher','Teacher'),('student','Student')]
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    role=models.CharField(max_length=10,choices=ROLE_CHOICES,default='student')
    roll_number=models.CharField(max_length=30,blank=True)
    class_name=models.CharField(max_length=60,blank=True)
    def __str__(self): return f'{self.user.username} ({self.role})'

class Student(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,null=True,blank=True)
    roll_number=models.CharField(max_length=30,unique=True)
    full_name=models.CharField(max_length=120)
    email=models.EmailField(blank=True)
    class_name=models.CharField(max_length=60)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.full_name} - {self.roll_number}'

class Subject(models.Model):
    name=models.CharField(max_length=100); code=models.CharField(max_length=20,unique=True); class_name=models.CharField(max_length=60,blank=True)
    def __str__(self): return f'{self.name} ({self.code})'

class TeacherAssignment(models.Model):
    teacher=models.ForeignKey(User,on_delete=models.CASCADE,related_name='subject_assignments')
    subject=models.ForeignKey(Subject,on_delete=models.CASCADE)
    class_name=models.CharField(max_length=60,blank=True)
    class Meta: unique_together=('teacher','subject','class_name')
    def __str__(self): return f'{self.teacher.username}: {self.subject}'

class Exam(models.Model):
    name=models.CharField(max_length=100); date=models.DateField(null=True,blank=True); class_name=models.CharField(max_length=60,blank=True)
    def __str__(self): return self.name

class Mark(models.Model):
    student=models.ForeignKey(Student,on_delete=models.CASCADE); subject=models.ForeignKey(Subject,on_delete=models.CASCADE); exam=models.ForeignKey(Exam,on_delete=models.CASCADE)
    marks_obtained=models.FloatField(); max_marks=models.FloatField(default=100)
    class Meta: unique_together=('student','subject','exam')
    def percentage(self): return self.marks_obtained/self.max_marks*100 if self.max_marks else 0
    def grade(self): return grade_for(self.percentage())
    def __str__(self): return f'{self.student} - {self.subject} - {self.exam}'

def grade_for(p):
    return 'A+' if p>=90 else 'A' if p>=80 else 'B' if p>=70 else 'C' if p>=60 else 'D' if p>=50 else 'E' if p>=40 else 'F'
