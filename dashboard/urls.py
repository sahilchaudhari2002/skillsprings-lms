from django.urls import path

from . import views

urlpatterns = [

    path(
        "dashboard-login/",
        views.admin_login,
        name="dashboard_login"
    ),

    path(
        "dashboard-logout/",
        views.admin_logout,
        name="dashboard_logout"
    ),

    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "admin-dashboard/courses/",
        views.course_list,
        name="dashboard_course_list"
    ),

    path(
        "admin-dashboard/courses/add/",
        views.course_create,
        name="dashboard_course_create"
    ),

    path(
        "admin-dashboard/courses/<int:pk>/edit/",
        views.course_edit,
        name="dashboard_course_edit"
    ),

    path(
        "admin-dashboard/courses/<int:pk>/delete/",
        views.course_delete,
        name="dashboard_course_delete"
    ),

]