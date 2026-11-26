# Generated initial migration for core models.
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateField(blank=True, null=True)),
                ('class_name', models.CharField(blank=True, max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('roll_number', models.CharField(max_length=30, unique=True)),
                ('full_name', models.CharField(max_length=120)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('class_name', models.CharField(max_length=60)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('class_name', models.CharField(blank=True, max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('student', 'Student')], default='student', max_length=10)),
                ('roll_number', models.CharField(blank=True, max_length=30)),
                ('class_name', models.CharField(blank=True, max_length=60)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='Mark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('marks_obtained', models.FloatField()),
                ('max_marks', models.FloatField(default=100)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.exam')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.student')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.subject')),
            ],
            options={'unique_together': {('student', 'subject', 'exam')}},
        ),
    ]
