import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User

from . import pdf
from .forms import ExamForm, QuestionForm
from .models import Attempt, Exam, Question

MANAGERS = (User.ADMIN, User.TEACHER)


# --------------------------------------------------------------------------- helpers
def manageable_exams(user):
    """Admins manage every exam; teachers manage only their own."""
    exams = Exam.objects.all()
    return exams if user.role == User.ADMIN else exams.filter(created_by=user)


def get_managed_exam(request, pk):
    return get_object_or_404(manageable_exams(request.user), pk=pk)


def ranked_attempts(exam):
    """Submitted attempts sorted by score (high first), then speed. Ties share a rank."""
    attempts = list(exam.attempts.filter(submitted_at__isnull=False).select_related("student", "exam"))
    attempts.sort(key=lambda a: (-a.score, a.time_taken_seconds))
    rank, previous = 0, None
    for position, attempt in enumerate(attempts, start=1):
        key = (attempt.score, attempt.time_taken_seconds)
        if key != previous:
            rank, previous = position, key
        attempt.rank = rank
    return attempts


def average_percentage(attempts):
    percentages = [a.percentage for a in attempts]
    return sum(percentages) / len(percentages) if percentages else None


def can_view_ranklist(user, exam):
    if user.role in MANAGERS:
        return manageable_exams(user).filter(pk=exam.pk).exists()
    return exam.attempts.filter(student=user, submitted_at__isnull=False).exists()


# --------------------------------------------------------------------------- dashboard
@login_required
def dashboard(request):
    user = request.user
    if user.role == User.ADMIN:
        context = {
            "stats": [
                ("Students", User.objects.filter(role=User.STUDENT).count()),
                ("Teachers", User.objects.filter(role=User.TEACHER).count()),
                ("Exams", Exam.objects.count()),
                ("Submissions", Attempt.objects.filter(submitted_at__isnull=False).count()),
            ],
            "recent": Attempt.objects.filter(submitted_at__isnull=False)
            .select_related("student", "exam")[:6],
        }
    elif user.role == User.TEACHER:
        exams = Exam.objects.filter(created_by=user)
        submitted = Attempt.objects.filter(exam__in=exams, submitted_at__isnull=False)
        avg = average_percentage(submitted)
        context = {
            "stats": [
                ("My exams", exams.count()),
                ("Questions", Question.objects.filter(exam__in=exams).count()),
                ("Submissions", submitted.count()),
                ("Average score", f"{avg:.0f}%" if avg is not None else "-"),
            ],
            "recent": submitted.select_related("student", "exam")[:6],
        }
    else:
        done = user.attempts.filter(submitted_at__isnull=False)
        taken_ids = user.attempts.values_list("exam_id", flat=True)
        open_exams = Exam.objects.filter(is_published=True).exclude(pk__in=taken_ids)
        open_exams = [e for e in open_exams.annotate(q=Count("questions")) if e.q]
        avg = average_percentage(done)
        context = {
            "stats": [
                ("Available exams", len(open_exams)),
                ("Completed", done.count()),
                ("Average score", f"{avg:.0f}%" if avg is not None else "-"),
                ("Exams passed", sum(1 for a in done.select_related("exam") if a.passed)),
            ],
            "open_exams": open_exams[:4],
            "recent": done.select_related("exam")[:5],
        }
    return render(request, "dashboard.html", context)


# --------------------------------------------------------------------------- exam management
@role_required(*MANAGERS)
def exam_list(request):
    exams = manageable_exams(request.user).select_related("created_by").annotate(
        question_count=Count("questions", distinct=True),
        attempt_count=Count("attempts", distinct=True),
    )
    return render(request, "exams/exam_list.html", {"exams": exams})


@role_required(*MANAGERS)
def exam_create(request):
    form = ExamForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        exam = form.save(commit=False)
        exam.created_by = request.user
        exam.save()
        messages.success(request, "Exam created. Now add your questions.")
        return redirect("exam_edit", pk=exam.pk)
    return render(request, "exams/exam_form.html", {"form": form, "exam": None})


@role_required(*MANAGERS)
def exam_edit(request, pk):
    exam = get_managed_exam(request, pk)
    form = ExamForm(request.POST or None, instance=exam)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Exam details saved.")
        return redirect("exam_edit", pk=exam.pk)
    return render(
        request,
        "exams/exam_form.html",
        {
            "form": form,
            "exam": exam,
            "questions": exam.questions.all(),
            "has_attempts": exam.attempts.exists(),
        },
    )


@role_required(*MANAGERS)
@require_POST
def exam_delete(request, pk):
    exam = get_managed_exam(request, pk)
    title = exam.title
    exam.delete()
    messages.success(request, f"“{title}” and its results were deleted.")
    return redirect("exam_list")


def _locked_response(request, exam):
    messages.error(
        request,
        "Students have already taken this exam, so its questions can no longer be changed.",
    )
    return redirect("exam_edit", pk=exam.pk)


@role_required(*MANAGERS)
def question_add(request, pk):
    exam = get_managed_exam(request, pk)
    if exam.attempts.exists():
        return _locked_response(request, exam)
    form = QuestionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        question = form.save(commit=False)
        question.exam = exam
        question.save()
        messages.success(request, "Question added.")
        if "save_add" in request.POST:
            return redirect("question_add", pk=exam.pk)
        return redirect("exam_edit", pk=exam.pk)
    return render(
        request,
        "form_page.html",
        {
            "form": form,
            "title": "Add a question",
            "subtitle": f"Exam: {exam.title}",
            "submit_label": "Save question",
            "extra_submit": ("save_add", "Save and add another"),
            "back_url": "exam_edit",
            "back_args": [exam.pk],
        },
    )


@role_required(*MANAGERS)
def question_edit(request, pk):
    question = get_object_or_404(Question.objects.select_related("exam"), pk=pk)
    exam = get_managed_exam(request, question.exam_id)
    if exam.attempts.exists():
        return _locked_response(request, exam)
    form = QuestionForm(request.POST or None, instance=question)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Question updated.")
        return redirect("exam_edit", pk=exam.pk)
    return render(
        request,
        "form_page.html",
        {
            "form": form,
            "title": "Edit question",
            "subtitle": f"Exam: {exam.title}",
            "submit_label": "Save changes",
            "back_url": "exam_edit",
            "back_args": [exam.pk],
        },
    )


@role_required(*MANAGERS)
@require_POST
def question_delete(request, pk):
    question = get_object_or_404(Question.objects.select_related("exam"), pk=pk)
    exam = get_managed_exam(request, question.exam_id)
    if exam.attempts.exists():
        return _locked_response(request, exam)
    question.delete()
    messages.success(request, "Question deleted.")
    return redirect("exam_edit", pk=exam.pk)


# --------------------------------------------------------------------------- results & rank list
@login_required
def exam_ranklist(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if not can_view_ranklist(request.user, exam):
        raise PermissionDenied
    attempts = ranked_attempts(exam)
    passed = sum(1 for a in attempts if a.passed)
    average = average_percentage(attempts)
    return render(
        request,
        "exams/ranklist.html",
        {
            "exam": exam,
            "attempts": attempts,
            "passed": passed,
            "average": average,
            "is_manager": request.user.role in MANAGERS,
        },
    )


@login_required
def exam_ranklist_pdf(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if not can_view_ranklist(request.user, exam):
        raise PermissionDenied
    response = HttpResponse(pdf.ranklist_pdf(exam, ranked_attempts(exam)), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="ranklist-exam-{exam.pk}.pdf"'
    return response


@role_required(User.ADMIN)
def all_results(request):
    attempts = Attempt.objects.filter(submitted_at__isnull=False).select_related("student", "exam")
    return render(request, "exams/all_results.html", {"attempts": attempts})


# --------------------------------------------------------------------------- student flow
@role_required(User.STUDENT)
def student_exams(request):
    attempts = {a.exam_id: a for a in request.user.attempts.all()}
    exams = Exam.objects.filter(is_published=True).annotate(question_count=Count("questions"))
    rows = []
    for exam in exams:
        if exam.question_count:
            rows.append({"exam": exam, "attempt": attempts.get(exam.pk)})
    return render(request, "exams/student_exams.html", {"rows": rows})


@role_required(User.STUDENT)
@require_POST
def exam_start(request, pk):
    exam = get_object_or_404(Exam, pk=pk, is_published=True)
    if not exam.questions.exists():
        messages.error(request, "This exam has no questions yet.")
        return redirect("student_exams")
    attempt, created = Attempt.objects.get_or_create(student=request.user, exam=exam)
    if attempt.is_submitted:
        messages.info(request, "You have already completed this exam.")
        return redirect("result_detail", pk=attempt.pk)
    return redirect("exam_take", pk=attempt.pk)


@role_required(User.STUDENT)
def exam_take(request, pk):
    attempt = get_object_or_404(
        Attempt.objects.select_related("exam"), pk=pk, student=request.user
    )
    if attempt.is_submitted:
        return redirect("result_detail", pk=attempt.pk)

    if request.method == "POST":
        selections = {}
        # Answers that arrive long after the deadline are ignored.
        if attempt.seconds_left >= -settings.EXAM_SUBMIT_GRACE_SECONDS:
            for key, value in request.POST.items():
                if key.startswith("q_") and key[2:].isdigit():
                    selections[int(key[2:])] = value
        attempt.finalize(selections)
        messages.success(request, "Your exam was submitted and graded.")
        return redirect("result_detail", pk=attempt.pk)

    if attempt.seconds_left <= 0:
        attempt.finalize({})
        messages.warning(request, "Time ran out before you submitted this exam.")
        return redirect("result_detail", pk=attempt.pk)

    questions = list(attempt.exam.questions.all())
    random.Random(attempt.pk).shuffle(questions)  # stable order per student
    return render(
        request,
        "exams/take.html",
        {"attempt": attempt, "exam": attempt.exam, "questions": questions},
    )


@role_required(User.STUDENT)
def my_results(request):
    attempts = request.user.attempts.filter(submitted_at__isnull=False).select_related("exam")
    return render(request, "exams/my_results.html", {"attempts": attempts})


def _get_visible_attempt(request, pk):
    attempt = get_object_or_404(
        Attempt.objects.select_related("exam", "student"), pk=pk, submitted_at__isnull=False
    )
    user = request.user
    if user.role == User.STUDENT and attempt.student_id != user.pk:
        raise PermissionDenied
    if user.role == User.TEACHER and attempt.exam.created_by_id != user.pk:
        raise PermissionDenied
    return attempt


@login_required
def result_detail(request, pk):
    attempt = _get_visible_attempt(request, pk)
    rank = next((a.rank for a in ranked_attempts(attempt.exam) if a.pk == attempt.pk), None)
    return render(
        request,
        "exams/result_detail.html",
        {
            "attempt": attempt,
            "answers": attempt.answers.select_related("question"),
            "rank": rank,
            "ring": int(attempt.percentage * 3.6),
        },
    )


@login_required
def result_pdf(request, pk):
    attempt = _get_visible_attempt(request, pk)
    response = HttpResponse(pdf.result_pdf(attempt), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="result-{attempt.student_id}-{attempt.exam_id}.pdf"'
    return response
