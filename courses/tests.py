from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Course, Enrollment, Lesson, LessonProgress, QuizQuestion, Result


class CourseFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="pass12345")
        self.course = Course.objects.create(
            title="Python Bootcamp",
            description="Learn Python from scratch.",
            image="https://example.com/python.jpg",
            duration="4 weeks",
            price=0,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Introduction",
            order=1,
            youtube_link="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )
        self.question = QuizQuestion.objects.create(
            course=self.course,
            question_text="What is Python?",
            option_a="A snake only",
            option_b="A programming language",
            option_c="A database",
            option_d="An editor",
            correct_option="B",
            order=1,
        )

    def test_free_course_redirects_to_login_when_logged_out(self):
        response = self.client.get(reverse("access_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_free_course_enrolls_logged_in_user(self):
        self.client.login(username="student", password="pass12345")
        response = self.client.get(reverse("access_course", args=[self.course.id]))
        self.assertRedirects(response, reverse("course_detail", args=[self.course.id]))
        self.assertTrue(
            Enrollment.objects.filter(user=self.user, course=self.course).exists()
        )

    def test_quiz_pass_creates_certificate_eligible_result(self):
        enrollment = Enrollment.objects.create(user=self.user, course=self.course, progress=100)
        LessonProgress.objects.create(enrollment=enrollment, lesson=self.lesson)
        self.client.login(username="student", password="pass12345")

        response = self.client.post(
            reverse("course_quiz", args=[self.course.id]),
            {f"question_{self.question.id}": "B"},
        )

        self.assertRedirects(response, reverse("dashboard"))
        result = Result.objects.get(user=self.user, course=self.course)
        self.assertTrue(result.passed)
        self.assertEqual(result.score, 100)
