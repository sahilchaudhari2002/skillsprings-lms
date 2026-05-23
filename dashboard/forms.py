from django import forms
from courses.models import Course, Lesson, QuizQuestion

class CourseForm(forms.ModelForm):

    class Meta:

        model = Course

        fields = "__all__"


class LessonForm(forms.ModelForm):

    class Meta:

        model = Lesson

        fields = "__all__"


class QuizForm(forms.ModelForm):

    class Meta:

        model = QuizQuestion

        fields = "__all__"