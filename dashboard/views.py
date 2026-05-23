from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required

from .decorators import superuser_required

from .forms import CourseForm

from courses.models import Course


@login_required
@superuser_required
def admin_dashboard(request):

    total_courses = Course.objects.count()

    courses = Course.objects.all().order_by("-id")[:5]

    context = {

        "total_courses": total_courses,
        "courses": courses

    }

    return render(
        request,
        "dashboard/index.html",
        context
    )


@login_required
@superuser_required
def course_list(request):

    courses = Course.objects.all().order_by("-id")

    return render(
        request,
        "dashboard/courses/list.html",
        {
            "courses": courses
        }
    )


@login_required
@superuser_required
def course_create(request):

    if request.method == "POST":

        form = CourseForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            return redirect("dashboard_course_list")

    else:

        form = CourseForm()

    return render(
        request,
        "dashboard/courses/create.html",
        {
            "form": form
        }
    )


@login_required
@superuser_required
def course_edit(request, pk):

    course = get_object_or_404(
        Course,
        pk=pk
    )

    if request.method == "POST":

        form = CourseForm(
            request.POST,
            request.FILES,
            instance=course
        )

        if form.is_valid():

            form.save()

            return redirect("dashboard_course_list")

    else:

        form = CourseForm(
            instance=course
        )

    return render(
        request,
        "dashboard/courses/edit.html",
        {
            "form": form,
            "course": course
        }
    )


@login_required
@superuser_required
def course_delete(request, pk):

    course = get_object_or_404(
        Course,
        pk=pk
    )

    if request.method == "POST":

        course.delete()

        return redirect("dashboard_course_list")

    return render(
        request,
        "dashboard/courses/delete.html",
        {
            "course": course
        }
    )
    
    
from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages


def admin_login(request):

    if request.method == "POST":

        username = request.POST.get("username")

        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.is_superuser:

            login(request, user)

            return redirect("admin_dashboard")

        else:

            messages.error(
                request,
                "Invalid admin credentials"
            )

    return render(
        request,
        "dashboard/login.html"
    )
    
def admin_logout(request):

    logout(request)

    return redirect("dashboard_login")