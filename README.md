# ExamPortal: Online Examination and Result Management System

A web-based exam platform built with **Django**. Teachers create timed multiple-choice exams, students take them online, and results are graded instantly with rank lists and downloadable PDF reports.

## Features

**Student**
- Self-registration with first name, last name, email and password
- Sign in with email and password
- Profile page to edit your name and change your password
- Browse published exams and start one (each exam can be taken once)
- Timed exam screen with a live countdown, progress bar, question navigator and auto-submit when time ends
- Instant score, pass/fail status, rank and full answer review
- Download result as PDF

**Teacher**
- Create, edit, publish and delete exams
- Add multiple-choice questions with marks and a correct answer
- View the rank list for each of their exams and review any student's answers
- Questions lock once students have attempted the exam, so results stay accurate

**Admin**
- Everything a teacher can do, across all exams
- Create teacher accounts and activate or deactivate users
- View all results across the portal
- Django's built-in admin panel at `/django-admin/`

**Other**
- Email-based login and role-based access control (admin, teacher, student)
- Server-enforced time limit (the deadline is calculated on the server, not the browser)
- Questions appear in a different order for each student
- Rank list with tie handling (same score and time share a rank)
- Responsive blue-and-white UI
- SQLite by default, MySQL supported through environment variables

## Tech stack

Python 3.10+, Django 4.2+, ReportLab (PDF), SQLite or MySQL, vanilla JavaScript and CSS.

## Getting started

```bash
git clone https://github.com/<your-username>/online-exam-portal.git
cd online-exam-portal

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations accounts exams
python manage.py migrate
python manage.py seed_demo      # optional: demo users and a sample exam
python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in.

| Role    | Email                | Password     |
|---------|----------------------|--------------|
| Admin   | `admin@example.com`  | `admin123`   |
| Teacher | `ravi@example.com`   | `teacher123` |
| Student | `meena@example.com`  | `student123` |

These accounts are for local demos only. Never create them on a public server.

To create your own admin instead: `python manage.py createsuperuser` (enter an email address, because that is what you sign in with).

## Using MySQL

Install the driver (`pip install mysqlclient`), create an empty database, then set:

```bash
export DB_ENGINE=mysql DB_NAME=exam_portal DB_USER=root DB_PASSWORD=yourpassword DB_HOST=127.0.0.1
```

and run `migrate` again.

## Project structure

```
config/      Django settings and root URLs
accounts/    Custom user model (roles), login, registration, user management
exams/       Exams, questions, attempts, grading, rank lists, PDF reports
templates/   HTML templates (base layouts, dashboards, exam screens)
static/      CSS design system and the exam-taking JavaScript
```

## How grading works

1. A student starts an exam, which creates an `Attempt` with a start time.
2. The server computes the deadline from the exam duration.
3. On submit (or automatic timeout) each answer is compared with the correct option and the score is stored.
4. Answers sent more than 60 seconds after the deadline are ignored (configurable with `EXAM_SUBMIT_GRACE_SECONDS`).

## Ideas for future work

- Question bank and CSV import of questions
- Scheduled start and end windows for each exam
- Tab-switch detection and other proctoring checks
- Charts for score distribution
- Email notifications and password reset
- REST API with Django REST Framework
- Automated tests and CI

## License

MIT
