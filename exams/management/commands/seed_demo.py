from django.core.management.base import BaseCommand

from accounts.models import User
from exams.models import Exam, Question

QUESTIONS = [
    ("Which keyword defines a function in Python?", ["func", "def", "lambda only", "function"], "B"),
    ("What is the output of len([1, 2, 3])?", ["2", "3", "4", "Error"], "B"),
    ("Which data type is immutable in Python?", ["list", "dict", "tuple", "set"], "C"),
    ("Which HTTP method is normally used to submit a form that changes data?", ["GET", "POST", "HEAD", "TRACE"], "B"),
    ("What does SQL stand for?", ["Structured Query Language", "Simple Question Logic", "Sequential Query List", "Standard Quick Language"], "A"),
    ("Which of these is a Django ORM method for fetching one object?", ["fetch()", "get()", "pull()", "find_one_only()"], "B"),
    ("What is the time complexity of binary search?", ["O(n)", "O(n log n)", "O(log n)", "O(1)"], "C"),
    ("Which symbol starts a comment in Python?", ["//", "#", "--", "/*"], "B"),
]

DEMO_USERS = [
    # email, password, first name, last name, role
    ("admin@example.com", "admin123", "Asha", "Admin", User.ADMIN),
    ("ravi@example.com", "teacher123", "Ravi", "Kumar", User.TEACHER),
    ("meena@example.com", "student123", "Meena", "Iyer", User.STUDENT),
]


class Command(BaseCommand):
    help = "Create demo users and a sample exam so the portal can be explored immediately."

    def handle(self, *args, **options):
        users = {}
        for email, password, first, last, role in DEMO_USERS:
            user, _ = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": first, "last_name": last, "role": role},
            )
            user.email = email
            user.role = role
            if role == User.ADMIN:
                user.is_staff = user.is_superuser = True
            user.set_password(password)
            user.save()
            users[role] = user

        exam, created = Exam.objects.get_or_create(
            title="Programming Fundamentals Quiz",
            defaults={
                "description": "A short quiz on Python, SQL and web basics. Answer every question before time runs out.",
                "duration_minutes": 10,
                "pass_percentage": 50,
                "is_published": True,
                "created_by": users[User.TEACHER],
            },
        )
        if created:
            for text, options, correct in QUESTIONS:
                Question.objects.create(
                    exam=exam, text=text, option_a=options[0], option_b=options[1],
                    option_c=options[2], option_d=options[3], correct_option=correct, marks=1,
                )

        self.stdout.write(self.style.SUCCESS("Demo data ready. Sign in with:"))
        for email, password, _, _, role in DEMO_USERS:
            self.stdout.write(f"  {role:<8} {email}  /  {password}")
