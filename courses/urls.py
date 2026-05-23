from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("course/<int:id>/", views.course_detail, name="course_detail"),
    path("course/<int:id>/access/", views.access_course, name="access_course"),
    path("course/<int:id>/buy/", views.buy_course, name="buy_course"),
    path("course/<int:id>/payment-success/", views.payment_success, name="payment_success"),
    path("lesson/<int:lesson_id>/complete/", views.complete_lesson, name="complete_lesson"),
    path("course/<int:id>/quiz/", views.course_quiz, name="course_quiz"),
    path("certificate/<int:id>/", views.download_certificate, name="certificate"),
    path("verify/<uuid:cert_id>/", views.verify_certificate, name="verify_certificate"),
    path(
    'quiz/<int:course_id>/',
    views.course_quiz,
    name='course_quiz'
),
   
path('forgot-password/', views.forgot_password, name='forgot_password'),

path('verify-otp/', views.verify_otp, name='verify_otp'),

path('reset-password/', views.reset_password, name='reset_password'),
path('login/', views.user_login, name='login'),

 
path(
    "admin-dashboard/",
    views.admin_dashboard,
    name="admin_dashboard"
),
    
 
# =========================================
# SEO PAGES
# =========================================

path(
    'about/',
    views.about,
    name='about'
),

path(
    'contact/',
    views.contact,
    name='contact'
),

path(
    'privacy-policy/',
    views.privacy_policy,
    name='privacy_policy'
),

path(
    'refund-policy/',
    views.refund_policy,
    name='refund_policy'
),

path(
    'terms-and-conditions/',
    views.terms_conditions,
    name='terms_conditions'
),

path(
    'faq/',
    views.faq,
    name='faq'
),
 

    
]
