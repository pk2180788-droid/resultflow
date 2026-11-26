from django import forms
from django.contrib.auth.models import User
from .models import Student,Subject,Exam,Mark,Profile,TeacherAssignment
class StudentForm(forms.ModelForm):
 class Meta: model=Student; fields=['roll_number','full_name','email','class_name']
class SubjectForm(forms.ModelForm):
 class Meta: model=Subject; fields=['name','code','class_name']
class ExamForm(forms.ModelForm):
 class Meta: model=Exam; fields=['name','date','class_name']; widgets={'date':forms.DateInput(attrs={'type':'date'})}
class MarkForm(forms.ModelForm):
 class Meta: model=Mark; fields=['student','subject','exam','marks_obtained','max_marks']
class AccountForm(forms.Form):
 username=forms.CharField(); password=forms.CharField(widget=forms.PasswordInput); full_name=forms.CharField(); email=forms.EmailField(required=False); role=forms.ChoiceField(choices=[('teacher','Teacher'),('student','Student')]); roll_number=forms.CharField(required=False); class_name=forms.CharField(required=False)
class AssignmentForm(forms.ModelForm):
 class Meta: model=TeacherAssignment; fields=['teacher','subject','class_name']
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs); self.fields['teacher'].queryset=User.objects.filter(profile__role='teacher')
