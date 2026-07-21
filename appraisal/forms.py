from django import forms
from .models import Appraisal



# =============================================================================
# FILE: appraisal/forms.py
# WHAT THIS FILE DOES:
#   Defines the forms used throughout the project.
#   There are three forms, one for each stage of the workflow:
#     1. PublicAppraisalForm  — employee fills this in (NO login needed)
#     2. TeamLeadReviewForm   — team lead adds their comment and rating
#     3. HRReviewForm         — HR adds the final comment and decision
# =============================================================================


# -----------------------------------------------------------------------------
# FORM 1: PublicAppraisalForm
# Used by employees who fill in the appraisal form WITHOUT logging in.
# They just enter their name, department, and all their appraisal answers.
# This is a plain Form (not a ModelForm) because we handle saving manually
# in the view so we can control exactly what gets stored.
# -----------------------------------------------------------------------------
from django import forms
from .models import Appraisal


# =============================================================================
# FORM 1: PublicAppraisalForm
# Filled in by employees without logging in.
# Instead of writing paragraphs, employees now select a score from 1 to 5
# for each of the 9 performance categories.
# =============================================================================

# The rating choices shown in every dropdown
SCORE_CHOICES = [
    ('', '-- Select a rating --'),  # default empty option
    (5, '5 - Excellent'),
    (4, '4 - Good'),
    (3, '3 - Average'),
    (2, '2 - Below Average'),
    (1, '1 - Poor'),
]


class PublicAppraisalForm(forms.Form):

    # ── Personal details ──
    first_name = forms.CharField(
        max_length=100,
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Joseph',
        })
    )

    last_name = forms.CharField(
        max_length=100,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Smith',
        })
    )

    department = forms.CharField(
        max_length=100,
        label='Department',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Engineering, Finance, Sales',
        })
    )

    period = forms.CharField(
        max_length=100,
        label='Appraisal Period',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Q1 2025 or Annual 2025',
        })
    )

    # ── Self-Assessment Rating Fields ──
    # Each field is a dropdown where the employee selects 1 to 5.
    # The label is the category name shown on the form.
    # The help_text is the small description shown under the label.

    # 1. Punctuality & Attendance
    score_punctuality = forms.ChoiceField(
        choices=SCORE_CHOICES,
        label='Punctuality & Attendance',
        help_text='How consistently do you arrive on time and attend work?',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # 2. Quality of Work
    score_quality = forms.ChoiceField(
        choices=SCORE_CHOICES,
        label='Quality of Work',
        help_text='How would you rate the standard and accuracy of your work output?',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # 3. Teamwork & Collaboration
    score_teamwork = forms.ChoiceField(
        choices=SCORE_CHOICES,
        label='Teamwork & Collaboration',
        help_text='How well do you work with your colleagues and contribute to the team?',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # 4. Communication Skills
    score_communication = forms.ChoiceField(
        choices=SCORE_CHOICES,
        label='Communication Skills',
        help_text='How clearly and effectively do you communicate with others?',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # 5. Meeting Deadlines
    score_deadlines = forms.ChoiceField(
        choices=SCORE_CHOICES,
        label='Meeting Deadlines',
        help_text='How consistently do you complete your tasks on time?',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # 6. Problem Solving
    score_problem_solving = forms.ChoiceField(
        choices=SCORE_CHOICES,
        label='Problem Solving',
        help_text='How effectively do you identify and resolve challenges?',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # 7. Initiative & Creativity
    score_initiative = forms.ChoiceField(
        choices=SCORE_CHOICES,
        label='Initiative & Creativity',
        help_text='How often do you take initiative and bring new ideas to the table?',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # 8. Professionalism
    score_professionalism = forms.ChoiceField(
        choices=SCORE_CHOICES,
        label='Professionalism',
        help_text='How would you rate your conduct, attitude and behaviour at work?',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # 9. Adherence to Company Rules
    score_adherence = forms.ChoiceField(
        choices=SCORE_CHOICES,
        label='Adherence to Company Rules',
        help_text='How well do you follow company policies and procedures?',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Optional written comment — employee can add anything extra
    additional_comments = forms.CharField(
        label='Additional Comments',
        required=False,
        help_text='Optional — anything else you would like to add.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any extra comments you want to share...',
        })
    )

    # ── Custom validation ──
    # These run when form.is_valid() is called in the view.
    # We make sure the employee actually selected a rating for every category.

    def clean_score_punctuality(self):
        value = self.cleaned_data.get('score_punctuality')
        if not value:
            raise forms.ValidationError('Please select a rating for Punctuality & Attendance.')
        return int(value)  # convert from string to integer before saving

    def clean_score_quality(self):
        value = self.cleaned_data.get('score_quality')
        if not value:
            raise forms.ValidationError('Please select a rating for Quality of Work.')
        return int(value)

    def clean_score_teamwork(self):
        value = self.cleaned_data.get('score_teamwork')
        if not value:
            raise forms.ValidationError('Please select a rating for Teamwork & Collaboration.')
        return int(value)

    def clean_score_communication(self):
        value = self.cleaned_data.get('score_communication')
        if not value:
            raise forms.ValidationError('Please select a rating for Communication Skills.')
        return int(value)

    def clean_score_deadlines(self):
        value = self.cleaned_data.get('score_deadlines')
        if not value:
            raise forms.ValidationError('Please select a rating for Meeting Deadlines.')
        return int(value)

    def clean_score_problem_solving(self):
        value = self.cleaned_data.get('score_problem_solving')
        if not value:
            raise forms.ValidationError('Please select a rating for Problem Solving.')
        return int(value)

    def clean_score_initiative(self):
        value = self.cleaned_data.get('score_initiative')
        if not value:
            raise forms.ValidationError('Please select a rating for Initiative & Creativity.')
        return int(value)

    def clean_score_professionalism(self):
        value = self.cleaned_data.get('score_professionalism')
        if not value:
            raise forms.ValidationError('Please select a rating for Professionalism.')
        return int(value)

    def clean_score_adherence(self):
        value = self.cleaned_data.get('score_adherence')
        if not value:
            raise forms.ValidationError('Please select a rating for Adherence to Company Rules.')
        return int(value)


# =============================================================================
# FORM 2: TeamLeadReviewForm
# Team Lead adds their comment and overall rating.
# This has not changed.
# =============================================================================

class TeamLeadReviewForm(forms.ModelForm):

    class Meta:
        model = Appraisal
        fields = ['lead_comment', 'lead_rating']
        widgets = {
            'lead_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your assessment of the employee\'s performance...',
            }),
            'lead_rating': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'lead_comment': 'Your Review Comments',
            'lead_rating':  'Overall Performance Rating',
        }

    def clean_lead_rating(self):
        rating = self.cleaned_data.get('lead_rating')
        if not rating:
            raise forms.ValidationError('Please select a rating before submitting.')
        return rating

    def clean_lead_comment(self):
        comment = self.cleaned_data.get('lead_comment', '').strip()
        if len(comment) < 20:
            raise forms.ValidationError('Please write a more detailed comment (at least 20 characters).')
        return comment


# =============================================================================
# FORM 3: HRReviewForm
# HR adds the final comment and decision.
# This has not changed.
# =============================================================================

class HRReviewForm(forms.ModelForm):

    class Meta:
        model = Appraisal
        fields = ['hr_comment', 'hr_decision']
        widgets = {
            'hr_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write your HR observations or notes...',
            }),
            'hr_decision': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Approved for promotion, No action required, Salary review',
            }),
        }
        labels = {
            'hr_comment':  'HR Comments',
            'hr_decision': 'Decision / Outcome',
        }