from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # management (admin + teacher)
    path("manage/exams/", views.exam_list, name="exam_list"),
    path("manage/exams/new/", views.exam_create, name="exam_create"),
    path("manage/exams/<int:pk>/", views.exam_edit, name="exam_edit"),
    path("manage/exams/<int:pk>/delete/", views.exam_delete, name="exam_delete"),
    path("manage/exams/<int:pk>/questions/new/", views.question_add, name="question_add"),
    path("manage/questions/<int:pk>/edit/", views.question_edit, name="question_edit"),
    path("manage/questions/<int:pk>/delete/", views.question_delete, name="question_delete"),
    path("manage/results/", views.all_results, name="all_results"),
    # rank lists (managers + students who finished the exam)
    path("exams/<int:pk>/ranklist/", views.exam_ranklist, name="exam_ranklist"),
    path("exams/<int:pk>/ranklist/pdf/", views.exam_ranklist_pdf, name="exam_ranklist_pdf"),
    # student
    path("exams/", views.student_exams, name="student_exams"),
    path("exams/<int:pk>/start/", views.exam_start, name="exam_start"),
    path("attempts/<int:pk>/take/", views.exam_take, name="exam_take"),
    path("results/", views.my_results, name="my_results"),
    path("results/<int:pk>/", views.result_detail, name="result_detail"),
    path("results/<int:pk>/pdf/", views.result_pdf, name="result_pdf"),
]
