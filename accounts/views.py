from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import ProfileForm, StudentSignupForm, StyledPasswordChangeForm, TeacherCreateForm
from .models import User


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = StudentSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome! Your student account is ready.")
        return redirect("dashboard")
    return render(request, "accounts/register.html", {"form": form})


@role_required(User.ADMIN)
def user_list(request):
    role = request.GET.get("role", "")
    users = User.objects.order_by("role", "first_name", "username")
    if role in (User.ADMIN, User.TEACHER, User.STUDENT):
        users = users.filter(role=role)
    return render(request, "accounts/user_list.html", {"users": users, "role": role})


@role_required(User.ADMIN)
def teacher_create(request):
    form = TeacherCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"Teacher account created for {user.display_name}.")
        return redirect("user_list")
    return render(
        request,
        "form_page.html",
        {
            "form": form,
            "title": "Add a teacher",
            "subtitle": "Teachers can create exams and view results for their own exams.",
            "submit_label": "Create teacher",
            "back_url": "user_list",
        },
    )


@role_required(User.ADMIN)
@require_POST
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        state = "activated" if user.is_active else "deactivated"
        messages.success(request, f"{user.display_name} was {state}.")
    return redirect("user_list")


@login_required
def profile(request):
    profile_form = ProfileForm(instance=request.user)
    password_form = StyledPasswordChangeForm(request.user)

    if request.method == "POST":
        if "save_profile" in request.POST:
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your name was updated.")
                return redirect("profile")
        elif "change_password" in request.POST:
            password_form = StyledPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # keep the user signed in
                messages.success(request, "Your password was changed.")
                return redirect("profile")

    return render(
        request,
        "accounts/profile.html",
        {"profile_form": profile_form, "password_form": password_form},
    )
