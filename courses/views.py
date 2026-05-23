from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import (
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    Payment,
    Result,
)


PASS_PERCENTAGE = 60


def home(request):
    courses = Course.objects.all()
    free_courses_count = courses.filter(price=0).count()
    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(
            Enrollment.objects.filter(user=request.user).values_list("course_id", flat=True)
        )

    return render(
        request,
        "home.html",
        {
            "courses": courses,
            "free_courses_count": free_courses_count,
            "enrolled_ids": enrolled_ids,
        },
    )


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        return redirect("home")

    return render(request, "register.html")


def access_course(request, id):
    course = get_object_or_404(Course, id=id)

    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={reverse('access_course', args=[course.id])}")

    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if enrollment:
        return redirect("course_detail", id=course.id)

    if course.is_free:
        Enrollment.objects.get_or_create(user=request.user, course=course)
        return redirect("course_detail", id=course.id)

    return redirect("buy_course", id=course.id)


@login_required
def buy_course(request, id):
    course = get_object_or_404(Course, id=id)

    if Enrollment.objects.filter(user=request.user, course=course).exists():
        return redirect("course_detail", id=course.id)

    if course.is_free:
        Enrollment.objects.get_or_create(user=request.user, course=course)
        return redirect("course_detail", id=course.id)

    payment = None
    payment_error = ""

    try:
        import razorpay

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        payment = client.order.create(
            {
                "amount": course.price * 100,
                "currency": "INR",
                "payment_capture": "1",
            }
        )
        Payment.objects.create(
            user=request.user,
            course=course,
            amount=course.price,
            razorpay_order_id=payment["id"],
        )
    except Exception as exc:
        payment_error = str(exc)

    return render(
        request,
        "buy_course.html",
        {
            "course": course,
            "payment": payment,
            "payment_error": payment_error,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        },
    )


@login_required
def payment_success(request, id):
    course = get_object_or_404(Course, id=id)

    payment_id = request.GET.get("payment_id") or request.POST.get("razorpay_payment_id")
    order_id = request.GET.get("order_id") or request.POST.get("razorpay_order_id")
    signature = request.GET.get("signature") or request.POST.get("razorpay_signature")

    if not course.is_free:
        payment_obj = (
            Payment.objects.filter(
                user=request.user,
                course=course,
                razorpay_order_id=order_id or "",
            )
            .order_by("-created_at")
            .first()
        )

        if payment_obj:
            payment_obj.razorpay_payment_id = payment_id or payment_obj.razorpay_payment_id
            payment_obj.razorpay_signature = signature or payment_obj.razorpay_signature
            payment_obj.status = Payment.STATUS_SUCCESS
            payment_obj.save()

    Enrollment.objects.get_or_create(user=request.user, course=course)
    messages.success(request, "You are enrolled successfully.")
    return redirect("course_detail", id=course.id)


@login_required
def course_detail(request, id):
    course = get_object_or_404(Course, id=id)
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()

    if not enrollment:
        if course.is_free:
            enrollment = Enrollment.objects.create(user=request.user, course=course)
        else:
            return redirect("buy_course", id=course.id)

    lessons = list(course.lessons.all())
    current_lesson = None

    if lessons:
        lesson_id = request.GET.get("lesson")
        if lesson_id:
            current_lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        else:
            current_lesson = lessons[0]

    completed_lesson_ids = set(
        enrollment.lesson_progress.values_list("lesson_id", flat=True)
    )
    total_lessons = len(lessons)
    completed_count = len(completed_lesson_ids)
    progress = int((completed_count / total_lessons) * 100) if total_lessons else 0

    if enrollment.progress != progress:
        enrollment.progress = progress
        enrollment.save(update_fields=["progress"])

    result = Result.objects.filter(user=request.user, course=course).first()

    return render(
        request,
        "course_detail.html",
        {
            "course": course,
            "enrollment": enrollment,
            "lessons": lessons,
            "current_lesson": current_lesson,
            "completed_lesson_ids": completed_lesson_ids,
            "progress": progress,
            "quiz_ready": total_lessons > 0 and completed_count == total_lessons,
            "result": result,
            "pass_percentage": PASS_PERCENTAGE,
        },
    )

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import Lesson, LessonProgress, Enrollment

@login_required
def complete_lesson(request, lesson_id):

    if request.method == "POST":

        lesson = get_object_or_404(Lesson, id=lesson_id)

        enrollment = Enrollment.objects.get(
            user=request.user,
            course=lesson.course
        )

        # 🔷 SAVE COMPLETED LESSON
        LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )

        # 🔷 FIND NEXT LESSON
        next_lesson = Lesson.objects.filter(
            course=lesson.course,
            order__gt=lesson.order
        ).first()

        # 🔷 IF NEXT LESSON EXISTS
        if next_lesson:

            return redirect(
                f"/course/{lesson.course.id}/?lesson={next_lesson.id}"
            )

        # 🔷 IF NO NEXT LESSON → REDIRECT TO QUIZ
        return redirect(
            'course_quiz',
            course_id=lesson.course.id
        )

    return redirect('/')
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import (
    Course,
    Enrollment,
    Result,
    LessonProgress,
    QuizQuestion
)

PASS_PERCENTAGE = 60


@login_required
def course_quiz(request, course_id):

    # 🔷 GET COURSE
    course = get_object_or_404(
        Course,
        id=course_id
    )

    # 🔷 CHECK ENROLLMENT
    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=course
    )

    # 🔷 GET QUESTIONS
    questions = list(
        course.quiz_questions.all()
    )

    # 🔷 CHECK LESSON COMPLETION
    total_lessons = course.lessons.count()

    completed_count = LessonProgress.objects.filter(
        enrollment=enrollment
    ).count()

    # 🔷 PREVENT QUIZ BEFORE LESSON COMPLETE
    if total_lessons > 0 and completed_count < total_lessons:

        messages.warning(
            request,
            "Please complete all lessons before taking the quiz."
        )

        return redirect(
            'course_detail',
            id=course.id
        )

    # 🔷 QUIZ SUBMIT
    if request.method == "POST":

        total_questions = len(questions)

        correct_answers = 0

        # 🔷 CHECK ANSWERS
        for question in questions:

            selected_answer = request.POST.get(
                f"question_{question.id}"
            )

            if selected_answer == question.correct_option:
                correct_answers += 1

        # 🔷 SCORE
        if total_questions > 0:
            score = round(
                (correct_answers / total_questions) * 100,
                2
            )
        else:
            score = 0

        # 🔷 PASS/FAIL
        passed = score >= PASS_PERCENTAGE

        # 🔷 SAVE RESULT
        result, created = Result.objects.get_or_create(
    user=request.user,
    course=course,
    defaults={
        'score': score,
        'total_questions': total_questions,
        'passed': passed
    }
)

        result.score = score
        result.total_questions = total_questions
        result.passed = passed

        result.save()

        # 🔷 SUCCESS MESSAGE
        if passed:

            messages.success(
                request,
                f"🎉 You scored {score}% and unlocked your certificate."
            )

        else:

            messages.error(
                request,
                f"You scored {score}%. Minimum {PASS_PERCENTAGE}% required."
            )

        # 🔷 REDIRECT
        return redirect('dashboard')

    # 🔷 LOAD QUIZ PAGE
    return render(
        request,
        'quiz.html',
        {
            'course': course,
            'questions': questions,
            'pass_percentage': PASS_PERCENTAGE,
        }
    )

@login_required
def dashboard(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related("course")
    payments = Payment.objects.filter(user=request.user).select_related("course")
    results = Result.objects.filter(user=request.user).select_related("course")
    passed_course_ids = set(results.filter(passed=True).values_list("course_id", flat=True))

    completed_count = len(passed_course_ids)
    in_progress_count = sum(1 for enrollment in enrollments if enrollment.progress < 100)

    return render(
        request,
        "dashboard.html",
        {
            "enrollments": enrollments,
            "payments": payments,
            "results": results,
            "completed_count": completed_count,
            "in_progress_count": in_progress_count,
            "passed_course_ids": passed_course_ids,
        },
    )


# ============================================
# IMPORTS
# ============================================

from io import BytesIO
import os
import qrcode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .models import Course, Result


PASS_PERCENTAGE = 60


@login_required
def download_certificate(request, id):

    # =====================================================
    # GET COURSE
    # =====================================================

    course = get_object_or_404(
        Course,
        id=id
    )

    # =====================================================
    # GET RESULT
    # =====================================================

    result = get_object_or_404(
        Result,
        user=request.user,
        course=course
    )

    # =====================================================
    # VALIDATION
    # =====================================================

    if not result.passed:

        return HttpResponse(
            "Certificate not available.",
            status=403
        )

    if result.score < PASS_PERCENTAGE:

        return HttpResponse(
            "Minimum score not achieved.",
            status=403
        )

    # =====================================================
    # IMAGE PATHS
    # =====================================================

    logo_path = os.path.join(
        settings.BASE_DIR,
        "courses",
        "static",
        "images",
        "logo.png"
    )

    seal_path = os.path.join(
        settings.BASE_DIR,
        "courses",
        "static",
        "images",
        "seal.png"
    )

    # =====================================================
    # RESPONSE
    # =====================================================

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; filename="SkillSprings_Certificate.pdf"'
    )

    # =====================================================
    # PDF PAGE
    # =====================================================

    pdf = canvas.Canvas(
        response,
        pagesize=landscape(A4)
    )

    width, height = landscape(A4)

    # =====================================================
    # WHITE BACKGROUND
    # =====================================================

    pdf.setFillColor(
        colors.white
    )

    pdf.rect(
        0,
        0,
        width,
        height,
        fill=1
    )

    # =====================================================
    # OUTER BORDER
    # =====================================================

    pdf.setStrokeColor(
        colors.HexColor("#1e3a8a")
    )

    pdf.setLineWidth(4)

    pdf.rect(
        30,
        30,
        width - 60,
        height - 60
    )

    # =====================================================
    # INNER BORDER
    # =====================================================

    pdf.setStrokeColor(
        colors.HexColor("#cbd5e1")
    )

    pdf.setLineWidth(1)

    pdf.rect(
        42,
        42,
        width - 84,
        height - 84
    )

    # =====================================================
    # WATERMARK
    # =====================================================

    pdf.saveState()

    pdf.translate(
        width / 2,
        height / 2
    )

    pdf.rotate(30)

    pdf.setFont(
        "Helvetica-Bold",
        85
    )

    pdf.setFillColorRGB(
        0.90,
        0.92,
        0.96,
        alpha=0.10
    )

    pdf.drawCentredString(
        0,
        0,
        "SKILLSPRINGS"
    )

    pdf.restoreState()

    # =====================================================
    # LOGO
    # =====================================================

    if os.path.exists(logo_path):

        pdf.drawImage(
            logo_path,

            width / 2 - 90,

            height - 150,

            width=180,

            height=80,

            mask='auto'
        )

    # =====================================================
    # TITLE
    # =====================================================

    pdf.setFont(
        "Helvetica-Bold",
        34
    )

    pdf.setFillColor(
        colors.HexColor("#0f172a")
    )

    pdf.drawCentredString(
        width / 2,
        height - 205,
        "CERTIFICATE OF COMPLETION"
    )

    # =====================================================
    # SUBTITLE
    # =====================================================

    pdf.setFont(
        "Helvetica",
        16
    )

    pdf.setFillColor(
        colors.HexColor("#64748b")
    )

    pdf.drawCentredString(
        width / 2,
        height - 240,
        "This certificate is proudly awarded to"
    )

    # =====================================================
    # STUDENT NAME
    # =====================================================

    student_name = (
        request.user.username.upper()
    )

    pdf.setFont(
        "Helvetica-Bold",
        32
    )

    pdf.setFillColor(
        colors.HexColor("#1e3a8a")
    )

    pdf.drawCentredString(
        width / 2,
        height - 300,
        student_name
    )

    # =====================================================
    # LINE BELOW NAME
    # =====================================================

    pdf.setStrokeColor(
        colors.HexColor("#cbd5e1")
    )

    pdf.line(
        width / 2 - 170,
        height - 315,
        width / 2 + 170,
        height - 315
    )

    # =====================================================
    # COURSE TEXT
    # =====================================================

    pdf.setFont(
        "Helvetica",
        15
    )

    pdf.setFillColor(
        colors.HexColor("#334155")
    )

    pdf.drawCentredString(
        width / 2,
        height - 360,
        "for successfully completing the course"
    )

    # =====================================================
    # COURSE NAME
    # =====================================================

    pdf.setFont(
        "Helvetica-Bold",
        24
    )

    pdf.setFillColor(
        colors.HexColor("#0f172a")
    )

    pdf.drawCentredString(
        width / 2,
        height - 405,
        course.title
    )

    # =====================================================
    # SCORE
    # =====================================================

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.setFillColor(
        colors.HexColor("#16a34a")
    )

    pdf.drawCentredString(
        width / 2,
        height - 450,
        f"Final Score : {result.score}%"
    )

    # =====================================================
    # CERTIFICATE ID
    # =====================================================

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.setFillColor(
        colors.HexColor("#64748b")
    )

    pdf.drawCentredString(
        width / 2,
        height - 475,
        f"Certificate ID : {result.certificate_id}"
    )

    # =====================================================
    # QR CODE
    # =====================================================

    verify_url = request.build_absolute_uri(
        reverse(
            "verify_certificate",
            args=[result.certificate_id]
        )
    )

    qr = qrcode.make(
        verify_url
    )

    qr_buffer = BytesIO()

    qr.save(
        qr_buffer,
        format="PNG"
    )

    qr_buffer.seek(0)

    qr_image = ImageReader(
        qr_buffer
    )

    pdf.drawImage(
        qr_image,

        80,
        80,

        width=70,
        height=70
    )

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.setFillColor(
        colors.HexColor("#475569")
    )

    pdf.drawString(
        65,
        65,
        "Verify Certificate"
    )

    # =====================================================
    # SEAL BOTTOM RIGHT
    # =====================================================

    if os.path.exists(seal_path):

        pdf.drawImage(
            seal_path,

            width - 170,

            55,

            width=90,
            height=90,

            mask='auto'
        )

    # =====================================================
    # FOOTER
    # =====================================================

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.setFillColor(
        colors.HexColor("#64748b")
    )

    pdf.drawCentredString(
        width / 2,
        35,
        "SkillSprings • Professional Digital Certificate"
    )

    # =====================================================
    # SAVE
    # =====================================================

    pdf.showPage()

    pdf.save()

    return response


# ============================================
# VERIFY CERTIFICATE
# ============================================

def verify_certificate(request, cert_id):

    result = get_object_or_404(
        Result,
        certificate_id=cert_id,
        passed=True
    )

    return render(
        request,
        "verify.html",
        {
            "result": result
        }
    )



from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
import random

 
# ================= FORGOT PASSWORD OTP =================

def forgot_password(request):

    if request.method == "POST":

        username_or_email = request.POST.get("username")

        user = User.objects.filter(username=username_or_email).first()

        if not user:
            user = User.objects.filter(email=username_or_email).first()

        if user:

            otp = random.randint(100000, 999999)

            request.session['reset_otp'] = str(otp)
            request.session['reset_user_id'] = user.id

            send_mail(
                'SkillSprings Password Reset OTP',
                f'Your OTP code is: {otp}',
                'YOUR_GMAIL@gmail.com',
                [user.email],
                fail_silently=False,
            )

            messages.success(request, "OTP sent to your email.")

            return redirect('verify_otp')

        else:

            messages.error(request, "Username or email not found.")

    return render(request, 'forgot_password.html')


# ================= VERIFY OTP =================

def verify_otp(request):

    if request.method == "POST":

        entered_otp = request.POST.get("otp")

        session_otp = request.session.get("reset_otp")

        if entered_otp == session_otp:

            return redirect('reset_password')

        else:

            messages.error(request, "Invalid OTP")

    return render(request, 'verify_otp.html')


# ================= RESET PASSWORD =================
 
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.shortcuts import render, redirect

# ================= RESET PASSWORD =================

def reset_password(request):

    user_id = request.session.get("reset_user_id")

    if not user_id:

        messages.error(request, "Session expired.")

        return redirect("forgot_password")

    user = User.objects.get(id=user_id)

    if request.method == "POST":

        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # PASSWORD MATCH

        if password1 != password2:

            messages.error(request, "Passwords do not match.")

            return redirect("reset_password")

        # PASSWORD LENGTH

        if len(password1) < 6:

            messages.error(request, "Password too short.")

            return redirect("reset_password")

        # SAVE PASSWORD CORRECTLY

        user.password = make_password(password1)

        user.save()

        # CLEAR SESSION

        request.session.flush()

        messages.success(
            request,
            "Password updated successfully."
        )

        return redirect("login")

    return render(request, "reset_password.html")



 
from django.contrib.auth import authenticate, login

def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("home")

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

    return render(request, "registration/login.html")


 
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):

    context = {

        "total_students": 12400,
        "total_courses": 248,
        "total_revenue": 480000,
        "total_certificates": 5200,

    }

    return render(
        request,
        "admin_dashboard.html",
        context
    )

 
# =========================================
# SEO PAGES
# =========================================

def about(request):

    return render(
        request,
        'seo/about.html'
    )


 
from django.contrib import messages

from .models import ContactMessage


def contact(request):

    if request.method == 'POST':

        name = request.POST.get(
            'name'
        )

        email = request.POST.get(
            'email'
        )

        phone = request.POST.get(
            'phone'
        )

        message = request.POST.get(
            'message'
        )

        ContactMessage.objects.create(

            name=name,

            email=email,

            phone=phone,

            message=message
        )

        messages.success(

            request,

            'Message sent successfully!'
        )

    return render(

        request,

        'seo/contact.html'
    )
 



def privacy_policy(request):

    return render(
        request,
        'seo/privacy_policy.html'
    )


def refund_policy(request):

    return render(
        request,
        'seo/refund_policy.html'
    )


def terms_conditions(request):

    return render(
        request,
        'seo/terms_conditions.html'
    )


def faq(request):

    return render(
        request,
        'seo/faq.html'
    )
 
