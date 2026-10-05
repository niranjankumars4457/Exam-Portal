from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone


class Exam(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Shown to students before they start.")
    duration_minutes = models.PositiveIntegerField(default=30, help_text="Time limit in minutes.")
    pass_percentage = models.PositiveIntegerField(default=40, help_text="Minimum percentage needed to pass.")
    is_published = models.BooleanField(default=False, help_text="Students can only see published exams.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exams"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def total_marks(self):
        return self.questions.aggregate(total=Sum("marks"))["total"] or 0


class Question(models.Model):
    OPTIONS = ["A", "B", "C", "D"]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField("Question")
    option_a = models.CharField("Option A", max_length=300)
    option_b = models.CharField("Option B", max_length=300)
    option_c = models.CharField("Option C", max_length=300)
    option_d = models.CharField("Option D", max_length=300)
    correct_option = models.CharField(
        max_length=1, choices=[(o, f"Option {o}") for o in OPTIONS]
    )
    marks = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text[:60]

    def choices(self):
        return [
            ("A", self.option_a),
            ("B", self.option_b),
            ("C", self.option_c),
            ("D", self.option_d),
        ]

    def option_text(self, letter):
        return dict(self.choices()).get(letter, "")


class Attempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts"
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(fields=["student", "exam"], name="one_attempt_per_student_exam")
        ]

    def __str__(self):
        return f"{self.student} - {self.exam}"

    @property
    def is_submitted(self):
        return self.submitted_at is not None

    @property
    def deadline(self):
        return self.started_at + timedelta(minutes=self.exam.duration_minutes)

    @property
    def seconds_left(self):
        return int((self.deadline - timezone.now()).total_seconds())

    @property
    def percentage(self):
        if not self.total_marks:
            return 0
        return round(self.score * 100 / self.total_marks, 1)

    @property
    def passed(self):
        return self.is_submitted and self.percentage >= self.exam.pass_percentage

    @property
    def time_taken_seconds(self):
        if not self.submitted_at:
            return 0
        return int((self.submitted_at - self.started_at).total_seconds())

    @property
    def time_taken_display(self):
        minutes, seconds = divmod(self.time_taken_seconds, 60)
        return f"{minutes}m {seconds:02d}s"

    @transaction.atomic
    def finalize(self, selections):
        """Grade the attempt. `selections` maps question id -> chosen letter (A-D)."""
        if self.is_submitted:
            return
        score = total = 0
        for question in self.exam.questions.all():
            chosen = selections.get(question.id, "")
            if chosen not in Question.OPTIONS:
                chosen = ""
            correct = chosen == question.correct_option
            Answer.objects.create(
                attempt=self, question=question, selected=chosen, is_correct=correct
            )
            total += question.marks
            if correct:
                score += question.marks
        self.score = score
        self.total_marks = total
        self.submitted_at = timezone.now()
        self.save()


class Answer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["question_id"]

    @property
    def selected_text(self):
        return self.question.option_text(self.selected)

    @property
    def correct_text(self):
        return self.question.option_text(self.question.correct_option)
