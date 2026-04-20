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
            'placeholder': 'e.g. Engineering, Sales, Finance',
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

    # ── Self-appraisal sections ──
    self_summary = forms.CharField(
        label='Overall Performance Summary',
        help_text='Give a brief overview of how you performed this period.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Summarise your overall performance this period...',
        })
    )

    achievements = forms.CharField(
        label='Key Achievements',
        help_text='List the most important things you accomplished.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': '• Achievement 1\n• Achievement 2\n• Achievement 3',
        })
    )

    challenges = forms.CharField(
        label='Challenges Faced',
        help_text='Describe obstacles you encountered and how you dealt with them.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe any challenges and how you handled them...',
        })
    )

    goals_next_period = forms.CharField(
        label='Goals for Next Period',
        help_text='What do you want to achieve in the next period?',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '• Goal 1\n• Goal 2\n• Goal 3',
        })
    )

    # required=False means these fields are optional — the employee can leave them blank
    training_needs = forms.CharField(
        label='Training & Development Needs',
        required=False,
        help_text='Optional — any skills or courses you would like to pursue.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any training or development you would like...',
        })
    )

    additional_comments = forms.CharField(
        label='Additional Comments',
        required=False,
        help_text='Optional — anything else you would like to add.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Anything else you want to mention...',
        })
    )


# -----------------------------------------------------------------------------
# FORM 2: TeamLeadReviewForm
# Used by the Team Lead to add their comment and rating to an existing appraisal.
# This IS a ModelForm — it directly updates the Appraisal record in the database.
# Only the lead_comment and lead_rating fields are included so the lead
# cannot accidentally change the employee's answers.
# -----------------------------------------------------------------------------

class TeamLeadReviewForm(forms.ModelForm):

    class Meta:
        model = Appraisal
        # Only these two fields from the Appraisal model appear in this form
        fields = ['lead_comment', 'lead_rating']
        widgets = {
            'lead_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your assessment of the employee\'s performance...',
            }),
            # Select renders as a dropdown using the RATING_CHOICES from the model
            'lead_rating': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        labels = {
            'lead_comment': 'Your Review Comments',
            'lead_rating':  'Overall Performance Rating',
        }

    # ── Custom validation ──
    # These run automatically when form.is_valid() is called in the view.

    def clean_lead_rating(self):
        # Get the value the lead selected for the rating field
        rating = self.cleaned_data.get('lead_rating')
        # If they did not select a rating, stop and show this error message
        if not rating:
            raise forms.ValidationError('Please select a rating before submitting.')
        return rating

    def clean_lead_comment(self):
        # Get the comment text and remove leading/trailing spaces
        comment = self.cleaned_data.get('lead_comment', '').strip()
        # Require at least 20 characters so the lead writes something meaningful
        if len(comment) < 20:
            raise forms.ValidationError('Please write a more detailed comment (at least 20 characters).')
        return comment


# -----------------------------------------------------------------------------
# FORM 3: HRReviewForm
# Used by HR to add the final comment and decision to an appraisal.
# This IS a ModelForm — it directly updates the Appraisal record.
# Only hr_comment and hr_decision are included so HR cannot change
# the employee's answers or the lead's review.
# -----------------------------------------------------------------------------

class HRReviewForm(forms.ModelForm):

    class Meta:
        model = Appraisal
        # Only these two fields appear in the HR review form
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
