import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0009_lesson"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="enrollment",
            name="enrolled_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="lesson",
            name="description",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="lesson",
            name="is_preview",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="lesson",
            name="video",
            field=models.FileField(blank=True, null=True, upload_to="lessons/videos/"),
        ),
        migrations.AddField(
            model_name="payment",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="payment",
            name="razorpay_signature",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="result",
            name="attempted_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="result",
            name="passed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="result",
            name="total_questions",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="payment",
            name="razorpay_order_id",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.CreateModel(
            name="QuizQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question_text", models.TextField()),
                ("option_a", models.CharField(max_length=255)),
                ("option_b", models.CharField(max_length=255)),
                ("option_c", models.CharField(max_length=255)),
                ("option_d", models.CharField(max_length=255)),
                (
                    "correct_option",
                    models.CharField(
                        choices=[("A", "Option A"), ("B", "Option B"), ("C", "Option C"), ("D", "Option D")],
                        max_length=1,
                    ),
                ),
                ("order", models.PositiveIntegerField(default=0)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_questions", to="courses.course")),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("completed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "enrollment",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lesson_progress", to="courses.enrollment"),
                ),
                (
                    "lesson",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress_records", to="courses.lesson"),
                ),
            ],
            options={"ordering": ["-completed_at"]},
        ),
        migrations.AlterUniqueTogether(
            name="enrollment",
            unique_together={("user", "course")},
        ),
        migrations.AlterUniqueTogether(
            name="result",
            unique_together={("user", "course")},
        ),
        migrations.AlterUniqueTogether(
            name="lessonprogress",
            unique_together={("enrollment", "lesson")},
        ),
    ]
