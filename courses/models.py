import uuid

from django.contrib.auth.models import User
from django.db import models


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.URLField()
    duration = models.CharField(max_length=50)
    price = models.PositiveIntegerField(default=0)
    youtube_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "title"]

    def __str__(self):
        return self.title

    @property
    def is_free(self):
        return self.price == 0


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    progress = models.PositiveIntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-enrolled_at"]
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"


class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="results")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="results")
    score = models.FloatField()
    total_questions = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False)
    attempted_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-attempted_at"]
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.score}%)"


class Payment(models.Model):
    STATUS_PENDING = "Pending"
    STATUS_SUCCESS = "Success"
    STATUS_FAILED = "Failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="payments")
    amount = models.PositiveIntegerField()
    razorpay_order_id = models.CharField(max_length=200, blank=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.course.title} - {self.status}"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    youtube_link = models.URLField(blank=True)
    video = models.FileField(upload_to="lessons/videos/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def youtube_embed_url(self):
        if not self.youtube_link:
            return ""

        if "embed/" in self.youtube_link:
            return self.youtube_link

        video_id = ""
        if "v=" in self.youtube_link:
            video_id = self.youtube_link.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in self.youtube_link:
            video_id = self.youtube_link.split("youtu.be/")[-1].split("?")[0]

        return f"https://www.youtube.com/embed/{video_id}" if video_id else ""


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]
        unique_together = ("enrollment", "lesson")

    def __str__(self):
        return f"{self.enrollment.user.username} - {self.lesson.title}"


class QuizQuestion(models.Model):
    OPTION_A = "A"
    OPTION_B = "B"
    OPTION_C = "C"
    OPTION_D = "D"
    OPTION_CHOICES = [
        (OPTION_A, "Option A"),
        (OPTION_B, "Option B"),
        (OPTION_C, "Option C"),
        (OPTION_D, "Option D"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quiz_questions")
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course.title} - Q{self.order or self.pk}"



 
# =========================================
# CONTACT MESSAGE MODEL
# =========================================

class ContactMessage(models.Model):

    name = models.CharField(
        max_length=200
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=20
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.name
 
