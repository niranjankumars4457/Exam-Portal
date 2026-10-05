from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN, TEACHER, STUDENT = "admin", "teacher", "student"
    ROLE_CHOICES = [(ADMIN, "Admin"), (TEACHER, "Teacher"), (STUDENT, "Student")]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)

    def save(self, *args, **kwargs):
        # Accounts made with `createsuperuser` should land in the admin interface.
        if self.is_superuser:
            self.role = self.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin_role(self):
        return self.role == self.ADMIN

    @property
    def is_teacher_role(self):
        return self.role == self.TEACHER

    @property
    def is_student_role(self):
        return self.role == self.STUDENT

    @property
    def display_name(self):
        return self.get_full_name() or self.username
