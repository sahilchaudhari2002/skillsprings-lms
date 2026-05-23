from django.contrib import admin

from .models import Course, Enrollment, Lesson, LessonProgress, Payment, QuizQuestion, Result


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "duration", "created_at")
    search_fields = ("title", "description")
    inlines = [LessonInline, QuizQuestionInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "progress", "enrolled_at")
    list_filter = ("course",)
    search_fields = ("user__username", "course__title")


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "score", "passed", "attempted_at")
    list_filter = ("passed", "course")
    search_fields = ("user__username", "course__title", "certificate_id")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "amount", "status", "created_at")
    list_filter = ("status", "course")
    search_fields = ("user__username", "course__title", "razorpay_order_id", "razorpay_payment_id")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "is_preview")
    list_filter = ("course", "is_preview")
    search_fields = ("title", "course__title")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "lesson", "completed_at")
    list_filter = ("lesson__course",)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("course", "order", "question_text", "correct_option")
    list_filter = ("course",)



 
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.db.models import Sum
from django.template.response import TemplateResponse

from .models import *


# =========================================
# CUSTOM ADMIN SITE
# =========================================

class SkillSpringsAdminSite(AdminSite):

    site_header = "SkillSprings Admin"
    site_title = "SkillSprings Admin"
    index_title = "Premium Dashboard"

    def index(self, request, extra_context=None):

        total_users = User.objects.count()

        total_courses = Course.objects.count()

        total_enrollments = Enrollment.objects.count()

        total_revenue = (
            Payment.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0
        )

        context = {

            **self.each_context(request),

            "total_users": total_users,

            "total_courses": total_courses,

            "total_enrollments": total_enrollments,

            "total_revenue": total_revenue,
        }

        return TemplateResponse(
            request,
            "admin/index.html",
            context
        )


# =========================================
# CREATE ADMIN SITE OBJECT
# =========================================

admin_site = SkillSpringsAdminSite(
    name='skillsprings_admin'
)


# =========================================
# COURSE ADMIN
# =========================================

class CourseAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'price',
    )

    search_fields = (
        'title',
    )


# =========================================
# PAYMENT ADMIN
# =========================================

class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'amount',
    )


# =========================================
# REGISTER MODELS
# =========================================

admin_site.register(
    Course,
    CourseAdmin
)

admin_site.register(
    Payment,
    PaymentAdmin
)

admin_site.register(Enrollment)

admin_site.register(Lesson)

admin_site.register(LessonProgress)

admin_site.register(QuizQuestion)

admin_site.register(Result)


 
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):

    list_display = (

        'name',

        'email',

        'phone',

        'created_at'
    )

    search_fields = (

        'name',

        'email',

        'phone'
    )
 
