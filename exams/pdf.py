"""PDF generation for result reports and rank lists (ReportLab)."""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BLUE = colors.HexColor("#1d4ed8")
INK = colors.HexColor("#0f2a5c")
LINE = colors.HexColor("#dbe4f3")
SOFT = colors.HexColor("#eff6ff")
GREEN = colors.HexColor("#15803d")
RED = colors.HexColor("#b91c1c")

_base = getSampleStyleSheet()
TITLE = ParagraphStyle("T", parent=_base["Title"], textColor=INK, fontSize=20, alignment=0, spaceAfter=2)
SUB = ParagraphStyle("S", parent=_base["Normal"], textColor=colors.HexColor("#5b6b8c"), fontSize=10)
H2 = ParagraphStyle("H2", parent=_base["Heading2"], textColor=INK, fontSize=13, spaceBefore=14)
CELL = ParagraphStyle("C", parent=_base["Normal"], fontSize=9, leading=12)


def _build(story):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )
    doc.build(story)
    return buffer.getvalue()


def _table(data, widths, extra=None):
    table = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    table.setStyle(TableStyle(style + (extra or [])))
    return table


def result_pdf(attempt):
    exam, student = attempt.exam, attempt.student
    verdict = "PASSED" if attempt.passed else "NOT PASSED"
    verdict_color = GREEN if attempt.passed else RED

    story = [
        Paragraph("Result report", TITLE),
        Paragraph(f"{exam.title}", SUB),
        Spacer(1, 10),
    ]
    summary = [
        ["Student", student.display_name, "Email", student.email or student.username],
        ["Score", f"{attempt.score} / {attempt.total_marks}", "Percentage", f"{attempt.percentage}%"],
        ["Time taken", attempt.time_taken_display, "Pass mark", f"{exam.pass_percentage}%"],
        ["Submitted", attempt.submitted_at.astimezone().strftime("%d %b %Y, %I:%M %p"), "Result", verdict],
    ]
    table = Table(summary, colWidths=[28 * mm, 55 * mm, 28 * mm, 55 * mm])
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), INK),
        ("TEXTCOLOR", (2, 0), (2, -1), INK),
        ("TEXTCOLOR", (3, 3), (3, 3), verdict_color),
        ("FONTNAME", (3, 3), (3, 3), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 0.8, LINE),
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [table, Paragraph("Question review", H2)]

    rows = [["#", "Question", "Your answer", "Correct answer"]]
    extra = []
    for i, answer in enumerate(attempt.answers.select_related("question"), start=1):
        mine = f"{answer.selected}. {answer.selected_text}" if answer.selected else "Not answered"
        right = f"{answer.question.correct_option}. {answer.correct_text}"
        mine_color = "#15803d" if answer.is_correct else "#b91c1c"
        rows.append([
            str(i),
            Paragraph(escape(answer.question.text), CELL),
            Paragraph(f'<font color="{mine_color}">{escape(mine)}</font>', CELL),
            Paragraph(escape(right), CELL),
        ])
    story.append(_table(rows, [10 * mm, 74 * mm, 45 * mm, 45 * mm], extra))
    return _build(story)


def ranklist_pdf(exam, attempts):
    story = [
        Paragraph("Rank list", TITLE),
        Paragraph(f"{exam.title} - pass mark {exam.pass_percentage}%", SUB),
        Spacer(1, 10),
    ]
    rows = [["Rank", "Student", "Score", "Percentage", "Time", "Result"]]
    extra = []
    for i, a in enumerate(attempts, start=1):
        rows.append([
            str(a.rank), a.student.display_name, f"{a.score} / {a.total_marks}",
            f"{a.percentage}%", a.time_taken_display, "Pass" if a.passed else "Fail",
        ])
        extra.append(("TEXTCOLOR", (5, i), (5, i), GREEN if a.passed else RED))
    if len(rows) == 1:
        rows.append(["", "No submissions yet", "", "", "", ""])
    story.append(_table(rows, [16 * mm, 56 * mm, 25 * mm, 25 * mm, 28 * mm, 20 * mm], extra))
    return _build(story)
