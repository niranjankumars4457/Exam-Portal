from django import forms

from accounts.forms import StyledFormMixin

from .models import Exam, Question


class ExamForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["title", "description", "duration_minutes", "pass_percentage", "is_published"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields["is_published"].label = "Publish"

    def clean_duration_minutes(self):
        value = self.cleaned_data["duration_minutes"]
        if not 1 <= value <= 300:
            raise forms.ValidationError("Choose a duration between 1 and 300 minutes.")
        return value

    def clean_pass_percentage(self):
        value = self.cleaned_data["pass_percentage"]
        if value > 100:
            raise forms.ValidationError("Pass percentage cannot be more than 100.")
        return value


class QuestionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "option_a", "option_b", "option_c", "option_d", "correct_option", "marks"]
        widgets = {"text": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields["marks"].min_value = 1

    def clean_marks(self):
        value = self.cleaned_data["marks"]
        if value < 1:
            raise forms.ValidationError("Marks must be at least 1.")
        return value
