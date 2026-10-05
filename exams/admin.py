from django.contrib import admin

from .models import Answer, Attempt, Exam, Question


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "duration_minutes", "is_published", "created_at")
    list_filter = ("is_published",)
    inlines = [QuestionInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "score", "total_marks", "submitted_at")
    list_filter = ("exam",)


admin.site.register(Answer)
