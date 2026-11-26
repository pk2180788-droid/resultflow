from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from .models import Student, Subject, Exam, Mark, Profile, TeacherAssignment, grade_for
from .forms import StudentForm, SubjectForm, ExamForm, MarkForm, AccountForm, AssignmentForm
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from io import BytesIO


# =========================================================
# ROLE MANAGEMENT
# =========================================================

def role(user):
    if user.is_superuser:
        return 'admin'

    try:
        return user.profile.role
    except Profile.DoesNotExist:
        return 'student'


def login_view(request):
    if request.method == 'POST':
        u = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if u:
            login(request, u)
            return redirect('dashboard')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard(request):

    r = role(request.user)

    # STUDENT DASHBOARD
    if r == 'student':

        student = Student.objects.filter(user=request.user).first()

        if not student:
            return render(
                request,
                'core/student_dashboard.html',
                {
                    'student': None,
                    'marks': [],
                    'percentage': 0,
                    'grade': '—',
                    'status': 'Pending'
                }
            )

        ms = Mark.objects.filter(student=student).select_related(
            'subject', 'exam'
        )

        total = sum(m.marks_obtained for m in ms)
        maximum = sum(m.max_marks for m in ms)

        pct = round(total / maximum * 100, 2) if maximum else 0

        return render(
            request,
            'core/student_dashboard.html',
            {
                'student': student,
                'marks': ms,
                'percentage': pct,
                'grade': grade_for(pct),
                'status': 'Pass' if pct >= 40 else 'Fail'
            }
        )

    # TEACHER DASHBOARD
    if r == 'teacher':

        assigned = TeacherAssignment.objects.filter(
            teacher=request.user
        ).select_related('subject')

        subs = [a.subject for a in assigned]

        marks = Mark.objects.filter(
            subject__in=subs
        ).select_related('student', 'subject', 'exam')

        assigned_classes = [
            a.class_name for a in assigned if a.class_name
        ]

        teacher_students = Student.objects.filter(
            class_name__in=assigned_classes
        ).distinct()

        return render(
            request,
            'core/teacher_dashboard.html',
            {
                'assignments': assigned,
                'marks': marks,
                'students': teacher_students,
                'total_students': teacher_students.count(),
                'total_subjects': len(subs),
                'total_exams': Exam.objects.filter(
                    class_name__in=assigned_classes
                ).count(),
                'total_marks': marks.count()
            }
        )

    # ADMIN DASHBOARD

    marks_queryset = Mark.objects.select_related(
        'student', 'subject', 'exam'
    )

    students_count = Student.objects.count()
    subjects_count = Subject.objects.count()
    exams_count = Exam.objects.count()
    teachers_count = Profile.objects.filter(role='teacher').count()

    all_marks = list(marks_queryset)

    avg = round(
        sum(m.percentage() for m in all_marks) / len(all_marks),
        2
    ) if all_marks else 0

    rows = []

    for st in Student.objects.all():

        sm = [m for m in all_marks if m.student_id == st.id]

        if sm:

            total = sum(m.marks_obtained for m in sm)
            maximum = sum(m.max_marks for m in sm)

            pct = round(total / maximum * 100, 1) if maximum else 0

            rows.append({
                'student': st,
                'total': total,
                'maximum': maximum,
                'percent': pct,
                'grade': grade_for(pct),
                'status': 'Pass' if pct >= 40 else 'Fail'
            })

    rows.sort(
        key=lambda x: x['student'].created_at,
        reverse=True
    )

    grade_counts = {
        g: 0 for g in ['A+', 'A', 'B', 'C', 'D', 'E', 'F']
    }

    for x in rows:
        grade_counts[x['grade']] += 1

    passed = sum(1 for x in rows if x['status'] == 'Pass')
    failed = len(rows) - passed

    pass_rate = round(passed / len(rows) * 100) if rows else 0

    return render(
        request,
        'core/dashboard.html',
        {
            'total_students': students_count,
            'total_subjects': subjects_count,
            'total_exams': exams_count,
            'total_teachers': teachers_count,
            'avg': avg,
            'total_marks': len(all_marks),
            'recent': rows[:5],
            'grade_counts': grade_counts,
            'passed': passed,
            'failed': failed,
            'pass_rate': pass_rate,
            'top_students': [],
            'weak_students': [],
            'subject_labels': [],
            'subject_values': []
        }
    )


# =========================================================
# ADMIN ACCESS
# =========================================================

def admin_only(view):

    def wrapped(request, *args, **kwargs):

        if role(request.user) != 'admin':
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')

        return view(request, *args, **kwargs)

    return login_required(wrapped)


def teacher_allowed_subjects(user):

    return Subject.objects.filter(
        teacherassignment__teacher=user
    ).distinct()


# =========================================================
# ACCOUNTS
# =========================================================

@login_required
@admin_only
def accounts(request):

    form = AccountForm(request.POST or None)

    if form.is_valid():

        d = form.cleaned_data

        if User.objects.filter(username=d['username']).exists():

            form.add_error(
                'username',
                'Username already exists.'
            )

        else:

            u = User.objects.create_user(
                d['username'],
                d['email'],
                d['password']
            )

            u.first_name = d['full_name']
            u.save()

            Profile.objects.filter(user=u).update(
                role=d['role'],
                roll_number=d['roll_number'],
                class_name=d['class_name']
            )

            if d['role'] == 'student':

                Student.objects.create(
                    user=u,
                    roll_number=d['roll_number'],
                    full_name=d['full_name'],
                    email=d['email'],
                    class_name=d['class_name']
                )

            messages.success(request, 'Account created.')
            return redirect('accounts')

    return render(
        request,
        'core/accounts.html',
        {
            'form': form,
            'users': User.objects.filter(
                profile__role__in=['teacher', 'student']
            ).select_related('profile')
        }
    )


# =========================================================
# TEACHER SUBJECT ASSIGNMENTS
# =========================================================

@login_required
@admin_only
def assignments(request):

    form = AssignmentForm(request.POST or None)

    if form.is_valid():

        form.save()

        messages.success(request, 'Subject assigned.')

        return redirect('assignments')

    return render(
        request,
        'core/assignments.html',
        {
            'form': form,
            'assignments': TeacherAssignment.objects.select_related(
                'teacher', 'subject'
            )
        }
    )


# =========================================================
# STUDENTS
# =========================================================

@login_required
def students(request):

    if role(request.user) == 'teacher':
        return redirect('dashboard')

    q = request.GET.get('q', '')

    data = Student.objects.filter(
        Q(full_name__icontains=q) |
        Q(roll_number__icontains=q)
    )

    return render(
        request,
        'core/students.html',
        {
            'students': data.order_by('full_name'),
            'q': q
        }
    )


@login_required
def student_add(request):

    if role(request.user) != 'admin':
        return redirect('dashboard')

    f = StudentForm(request.POST or None)

    if f.is_valid():

        f.save()

        messages.success(request, 'Student added.')

        return redirect('students')

    return render(
        request,
        'core/student_form.html',
        {
            'form': f,
            'heading': 'Add Student'
        }
    )


@login_required
def student_edit(request, pk):

    if role(request.user) != 'admin':
        return redirect('dashboard')

    obj = get_object_or_404(Student, pk=pk)

    f = StudentForm(
        request.POST or None,
        instance=obj
    )

    if f.is_valid():

        f.save()

        return redirect('students')

    return render(
        request,
        'core/student_form.html',
        {
            'form': f,
            'heading': 'Edit Student'
        }
    )


@login_required
def student_delete(request, pk):

    if role(request.user) != 'admin':
        return redirect('dashboard')

    get_object_or_404(Student, pk=pk).delete()

    return redirect('students')


# =========================================================
# SUBJECTS
# =========================================================

@login_required
def subjects(request):

    r = role(request.user)

    if r == 'teacher':

        data = teacher_allowed_subjects(request.user)

        return render(
            request,
            'core/subjects.html',
            {
                'subjects': data,
                'form': None
            }
        )

    if r != 'admin':
        return redirect('dashboard')

    f = SubjectForm(request.POST or None)

    if f.is_valid():

        f.save()

        return redirect('subjects')

    return render(
        request,
        'core/subjects.html',
        {
            'subjects': Subject.objects.all(),
            'form': f
        }
    )


# =========================================================
# EXAMS
# =========================================================

@login_required
def exams(request):

    if role(request.user) != 'admin':
        return redirect('dashboard')

    f = ExamForm(request.POST or None)

    if f.is_valid():

        f.save()

        return redirect('exams')

    return render(
        request,
        'core/exams.html',
        {
            'exams': Exam.objects.all(),
            'form': f
        }
    )


# =========================================================
# MARKS
# =========================================================

@login_required
def marks(request):

    r = role(request.user)

    f = MarkForm(request.POST or None)

    if r == 'teacher':

        f.fields['subject'].queryset = teacher_allowed_subjects(
            request.user
        )

        if f.fields['subject'].queryset.exists():
            f.fields['student'].queryset = Student.objects.all()

    elif r != 'admin':

        return redirect('dashboard')

    if f.is_valid():

        d = f.cleaned_data

        if d['marks_obtained'] > d['max_marks']:

            f.add_error(
                'marks_obtained',
                'Cannot exceed maximum marks.'
            )

        elif r == 'teacher' and not teacher_allowed_subjects(
            request.user
        ).filter(pk=d['subject'].pk).exists():

            f.add_error(
                'subject',
                'Subject not assigned.'
            )

        else:

            f.save()

            return redirect('marks')

    queryset = Mark.objects.select_related(
        'student', 'subject', 'exam'
    )

    if r == 'teacher':

        queryset = queryset.filter(
            subject__in=teacher_allowed_subjects(request.user)
        )

    return render(
        request,
        'core/marks.html',
        {
            'marks': queryset.order_by('-id'),
            'form': f,
            'can_edit': r in ['admin', 'teacher']
        }
    )


@login_required
def mark_delete(request, pk):

    if role(request.user) not in ['admin', 'teacher']:
        return redirect('dashboard')

    m = get_object_or_404(Mark, pk=pk)

    if role(request.user) == 'teacher':

        if not teacher_allowed_subjects(
            request.user
        ).filter(pk=m.subject_id).exists():

            return redirect('marks')

    m.delete()

    return redirect('marks')


# =========================================================
# RESULTS
# =========================================================

@login_required
def results(request):

    if role(request.user) == 'student':
        return redirect('dashboard')

    rows = []

    qs = Student.objects.all()

    if role(request.user) == 'teacher':

        assigned_classes = TeacherAssignment.objects.filter(
            teacher=request.user
        ).values_list('class_name', flat=True)

        qs = qs.filter(
            class_name__in=assigned_classes
        )

    for s in qs:

        ms = Mark.objects.filter(
            student=s
        ).select_related('subject', 'exam')

        total = sum(m.marks_obtained for m in ms)
        maximum = sum(m.max_marks for m in ms)

        p = round(total / maximum * 100, 2) if maximum else 0

        if ms.exists():

            rows.append({
                'student': s,
                'total': total,
                'maximum': maximum,
                'percent': p,
                'grade': grade_for(p),
                'status': 'Pass' if p >= 40 else 'Fail',
                'marks': ms
            })

    return render(
        request,
        'core/results.html',
        {
            'rows': rows
        }
    )


def results_data():

    data = []

    for s in Student.objects.all():

        ms = Mark.objects.filter(
            student=s
        ).select_related('subject', 'exam')

        total = sum(m.marks_obtained for m in ms)
        maximum = sum(m.max_marks for m in ms)

        p = round(total / maximum * 100, 2) if maximum else 0

        if ms.exists():

            data.append({
                'student': s,
                'total': total,
                'maximum': maximum,
                'percent': p,
                'grade': grade_for(p),
                'status': 'Pass' if p >= 40 else 'Fail'
            })

    return data


# =========================================================
# EXCEL EXPORT
# =========================================================

@login_required
def export_excel(request):

    if role(request.user) == 'student':
        return redirect('dashboard')

    data = results_data()

    if role(request.user) == 'teacher':

        assigned_classes = TeacherAssignment.objects.filter(
            teacher=request.user
        ).values_list('class_name', flat=True)

        data = [
            x for x in data
            if x['student'].class_name in assigned_classes
        ]

    wb = Workbook()

    ws = wb.active

    ws.title = 'Results'

    ws.append([
        'Roll',
        'Name',
        'Class',
        'Total',
        'Maximum',
        'Percentage',
        'Grade',
        'Status'
    ])

    for x in data:

        ws.append([
            x['student'].roll_number,
            x['student'].full_name,
            x['student'].class_name,
            x['total'],
            x['maximum'],
            x['percent'],
            x['grade'],
            x['status']
        ])

    out = BytesIO()

    wb.save(out)

    response = HttpResponse(
        out.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = 'attachment; filename="results.xlsx"'

    return response


# =========================================================
# PDF CERTIFICATE DESIGN
# =========================================================

def draw_certificate(pdf, student, marks, exam_title='Academic Results'):

    width, height = A4

    navy = colors.HexColor('#18264A')
    purple = colors.HexColor('#4F46E5')
    light = colors.HexColor('#EEF2FF')
    green = colors.HexColor('#15803D')
    grey = colors.HexColor('#64748B')

    # PAGE BORDER

    pdf.setStrokeColor(purple)
    pdf.setLineWidth(2)

    pdf.rect(
        15 * mm,
        15 * mm,
        width - 30 * mm,
        height - 30 * mm
    )

    pdf.setStrokeColor(navy)
    pdf.setLineWidth(0.5)

    pdf.rect(
        18 * mm,
        18 * mm,
        width - 36 * mm,
        height - 36 * mm
    )

    # BRAND

    pdf.setFillColor(purple)

    pdf.setFont('Helvetica-Bold', 25)

    pdf.drawCentredString(
        width / 2,
        height - 45 * mm,
        'RESULTFLOW'
    )

    pdf.setFillColor(grey)

    pdf.setFont('Helvetica', 10)

    pdf.drawCentredString(
        width / 2,
        height - 53 * mm,
        'COLLEGE / INSTITUTION NAME'
    )

    pdf.setStrokeColor(purple)

    pdf.line(
        30 * mm,
        height - 58 * mm,
        width - 30 * mm,
        height - 58 * mm
    )

    # TITLE

    pdf.setFillColor(navy)

    pdf.setFont('Helvetica-Bold', 18)

    pdf.drawCentredString(
        width / 2,
        height - 75 * mm,
        'CERTIFICATE OF EXAMINATION RESULTS'
    )

    pdf.setFillColor(grey)

    pdf.setFont('Helvetica', 10)

    pdf.drawCentredString(
        width / 2,
        height - 83 * mm,
        'ACADEMIC PERFORMANCE CERTIFICATE'
    )

    # STUDENT

    pdf.setFillColor(navy)

    pdf.setFont('Helvetica', 12)

    pdf.drawCentredString(
        width / 2,
        height - 98 * mm,
        'This is to certify that'
    )

    pdf.setFillColor(purple)

    pdf.setFont('Helvetica-Bold', 22)

    pdf.drawCentredString(
        width / 2,
        height - 112 * mm,
        student.full_name[:50]
    )

    pdf.setFillColor(navy)

    pdf.setFont('Helvetica', 11)

    pdf.drawCentredString(
        width / 2,
        height - 122 * mm,
        f'Roll No. {student.roll_number}  |  Class: {student.class_name}'
    )

    pdf.drawCentredString(
        width / 2,
        height - 132 * mm,
        f'Examination: {exam_title[:70]}'
    )

    pdf.drawCentredString(
        width / 2,
        height - 142 * mm,
        'academic performance is presented below.'
    )

    # SUBJECT TABLE

    table_top = height - 158 * mm

    left = 28 * mm
    right = width - 28 * mm

    col1 = left
    col2 = left + 80 * mm
    col3 = left + 125 * mm
    col4 = right - 25 * mm

    pdf.setFillColor(purple)

    pdf.rect(
        left,
        table_top - 10 * mm,
        right - left,
        10 * mm,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(colors.white)

    pdf.setFont('Helvetica-Bold', 10)

    pdf.drawString(col1 + 3 * mm, table_top - 6.5 * mm, 'Subject')
    pdf.drawString(col2 + 3 * mm, table_top - 6.5 * mm, 'Exam')
    pdf.drawString(col3 + 3 * mm, table_top - 6.5 * mm, 'Marks')
    pdf.drawString(col4 + 3 * mm, table_top - 6.5 * mm, 'Grade')

    y = table_top - 10 * mm

    total = 0
    maximum = 0

    pdf.setFont('Helvetica', 9)

    for index, m in enumerate(marks):

        if y < 80 * mm:

            pdf.showPage()

            # Recreate page border on overflow page
            pdf.setStrokeColor(purple)
            pdf.setLineWidth(2)
            pdf.rect(
                15 * mm,
                15 * mm,
                width - 30 * mm,
                height - 30 * mm
            )

            y = height - 40 * mm

        row_height = 9 * mm

        if index % 2 == 0:
            pdf.setFillColor(light)
        else:
            pdf.setFillColor(colors.white)

        pdf.rect(
            left,
            y - row_height,
            right - left,
            row_height,
            fill=1,
            stroke=0
        )

        pdf.setFillColor(navy)

        pdf.drawString(
            col1 + 3 * mm,
            y - 6 * mm,
            m.subject.name[:30]
        )

        pdf.drawString(
            col2 + 3 * mm,
            y - 6 * mm,
            m.exam.name[:25]
        )

        pdf.drawString(
            col3 + 3 * mm,
            y - 6 * mm,
            f'{m.marks_obtained}/{m.max_marks}'
        )

        pdf.drawString(
            col4 + 3 * mm,
            y - 6 * mm,
            m.grade()
        )

        total += m.marks_obtained
        maximum += m.max_marks

        y -= row_height

    percentage = round(total / maximum * 100, 2) if maximum else 0

    overall_grade = grade_for(percentage)

    status = 'PASS' if percentage >= 40 else 'FAIL'

    # SUMMARY

    y -= 12 * mm

    summary_height = 30 * mm

    pdf.setFillColor(light)

    pdf.roundRect(
        left,
        y - summary_height,
        right - left,
        summary_height,
        5 * mm,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(green)

    pdf.setFont('Helvetica-Bold', 12)

    pdf.drawString(
        left + 5 * mm,
        y - 8 * mm,
        f'TOTAL: {total}/{maximum}'
    )

    pdf.drawString(
        left + 85 * mm,
        y - 8 * mm,
        f'PERCENTAGE: {percentage:.2f}%'
    )

    pdf.drawString(
        left + 5 * mm,
        y - 20 * mm,
        f'GRADE: {overall_grade}'
    )

    pdf.drawString(
        left + 85 * mm,
        y - 20 * mm,
        f'STATUS: {status}'
    )

    # SIGNATURES

    y -= 55 * mm

    pdf.setFillColor(grey)

    pdf.setFont('Helvetica', 10)

    pdf.drawString(
        left,
        y,
        'Exam Authority'
    )

    pdf.drawRightString(
        right,
        y,
        'Principal Signature'
    )

    pdf.setStrokeColor(grey)

    pdf.line(
        left,
        y - 12 * mm,
        left + 55 * mm,
        y - 12 * mm
    )

    pdf.line(
        right - 55 * mm,
        y - 12 * mm,
        right,
        y - 12 * mm
    )

    # FOOTER

    pdf.setFillColor(grey)

    pdf.setFont('Helvetica', 8)

    pdf.drawCentredString(
        width / 2,
        22 * mm,
        'Generated by ResultFlow Academic Management System'
    )


# =========================================================
# ADMIN / TEACHER PDF EXPORT
# =========================================================

@login_required
def export_pdf(request):

    r = role(request.user)

    if r == 'student':
        return redirect('dashboard')

    data = results_data()

    if r == 'teacher':

        assigned_classes = list(
            TeacherAssignment.objects.filter(
                teacher=request.user
            ).values_list('class_name', flat=True)
        )

        data = [
            x for x in data
            if x['student'].class_name in assigned_classes
        ]

    buf = BytesIO()

    pdf = canvas.Canvas(buf, pagesize=A4)

    pdf.setTitle('ResultFlow Examination Certificates')

    if not data:

        pdf.setFont('Helvetica-Bold', 18)

        pdf.drawCentredString(
            A4[0] / 2,
            A4[1] / 2,
            'No result records available.'
        )

    for index, x in enumerate(data):

        student = x['student']

        student_marks = Mark.objects.filter(
            student=student
        ).select_related('subject', 'exam')

        draw_certificate(
            pdf,
            student,
            student_marks,
            'Academic Results'
        )

        if index < len(data) - 1:
            pdf.showPage()

    pdf.save()

    response = HttpResponse(
        buf.getvalue(),
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        'attachment; filename="ResultFlow_Results_Certificates.pdf"'
    )

    return response


# =========================================================
# STUDENT INDIVIDUAL PDF
# =========================================================

@login_required
def student_pdf(request):

    if role(request.user) != 'student':
        return redirect('dashboard')

    s = get_object_or_404(
        Student,
        user=request.user
    )

    ms = Mark.objects.filter(
        student=s
    ).select_related(
        'subject',
        'exam'
    ).order_by(
        'exam__date',
        'subject__name'
    )

    buf = BytesIO()

    pdf = canvas.Canvas(buf, pagesize=A4)

    pdf.setTitle(f'Result - {s.full_name}')

    draw_certificate(
        pdf,
        s,
        ms,
        'Academic Results'
    )

    pdf.save()

    response = HttpResponse(
        buf.getvalue(),
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="Result_{s.roll_number}.pdf"'
    )

    return response