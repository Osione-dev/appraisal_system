from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# =============================================================================
# FILE: appraisal/models.py
# WHAT THIS FILE DOES:
#   Defines the database tables for the entire project.
#   There are two tables:
#     1. CustomUser  — stores all user accounts (employees, leads, HR)
#     2. Appraisal   — stores every appraisal form submitted
# =============================================================================


# -----------------------------------------------------------------------------
# TABLE 1: CustomUser
# We extend Django's built-in user model so we keep the default fields
# (username, password, email) and add our own (role, department, job_title).
# -----------------------------------------------------------------------------

class CustomUser(AbstractUser):

    # ── Role constants ──
    # We define these as constants so we never mistype a role name anywhere else.
    # Instead of writing 'team_lead' everywhere, we write CustomUser.ROLE_TEAM_LEAD
    ROLE_EMPLOYEE  = 'employee'
    ROLE_TEAM_LEAD = 'team_lead'
    ROLE_HR        = 'hr'

    # ROLE_CHOICES tells Django what the valid options are for the role field.
    # The first value ('employee') is what gets saved to the database.
    # The second value ('Employee') is what gets shown in forms and the admin panel.
    ROLE_CHOICES = [
        (ROLE_EMPLOYEE,  'Employee'),
        (ROLE_TEAM_LEAD, 'Team Lead'),
        (ROLE_HR,        'HR'),
    ]

    # ── Extra fields added to the default Django user ──
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    department = models.CharField(max_length=100, blank=True)  # blank=True means optional
    job_title  = models.CharField(max_length=100, blank=True)

    # ── Self-referencing foreign key ──
    # This links an employee to their team lead.
    # 'self' means it points to another row in the SAME CustomUser table.
    # null=True  → the field can be empty in the database
    # blank=True → the field is optional in forms
    # SET_NULL   → if the lead user is deleted, this field becomes null (employee stays)
    # related_name='team_members' → lets you do: lead_user.team_members.all()
    team_lead = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members',
        limit_choices_to={'role': ROLE_TEAM_LEAD}  # only show team leads in the dropdown
    )

    def __str__(self):
        # This controls how a user appears in the admin panel and dropdowns
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # ── Role helper properties ──
    # These let views write clean checks like:  if user.is_employee:
    # Instead of the longer version:           if user.role == 'employee':
    @property
    def is_employee(self):
        return self.role == self.ROLE_EMPLOYEE

    @property
    def is_team_lead(self):
        return self.role == self.ROLE_TEAM_LEAD

    @property
    def is_hr(self):
        return self.role == self.ROLE_HR


# -----------------------------------------------------------------------------
# TABLE 2: Appraisal
# Stores one complete appraisal form per employee per period.
# The same record is updated as it moves through the workflow:
#   Employee fills it → Lead reviews it → HR finalises it
# -----------------------------------------------------------------------------

class Appraisal(models.Model):

    # ── Status constants ──
    # These track where in the workflow pipeline the appraisal currently is.
    STATUS_DRAFT       = 'draft'        # Employee saved but not yet submitted
    STATUS_PENDING_LEAD = 'pending_lead' # Submitted by employee, waiting for lead
    STATUS_PENDING_HR  = 'pending_hr'   # Lead reviewed, waiting for HR
    STATUS_REVIEWED    = 'reviewed'     # HR has finalised — workflow complete

    STATUS_CHOICES = [
        (STATUS_DRAFT,        'Draft'),
        (STATUS_PENDING_LEAD, 'Awaiting Team Lead Review'),
        (STATUS_PENDING_HR,   'Awaiting HR Review'),
        (STATUS_REVIEWED,     'Reviewed'),
    ]

    # Rating scale used for all 9 self-assessment criteria
    SCORE_CHOICES = [
        (5, '5 - Excellent'),
        (4, '4 - Good'),
        (3, '3 - Average'),
        (2, '2 - Below Average'),
        (1, '1 - Poor'),
    ]
 
    # Rating scale used by the Team Lead
    RATING_CHOICES = [
        (5, '5 - Outstanding'),
        (4, '4 - Exceeds Expectations'),
        (3, '3 - Meets Expectations'),
        (2, '2 - Below Expectations'),
        (1, '1 - Needs Improvement'),
    ]
 
    # ── Who is involved ──
    employee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='appraisals',
        null=True, blank=True,
        limit_choices_to={'role': CustomUser.ROLE_EMPLOYEE}
    )
    # These two store the name and department for public submissions
    employee_name       = models.CharField(max_length=200, blank=True)
    employee_department = models.CharField(max_length=100, blank=True)
 
    reviewed_by_lead = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='lead_reviews',
        limit_choices_to={'role': CustomUser.ROLE_TEAM_LEAD}
    )
    reviewed_by_hr = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='hr_reviews',
        limit_choices_to={'role': CustomUser.ROLE_HR}
    )
 
    # ── General info ──
    period = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_LEAD
    )
 
    # ── SECTION 1: Self-Assessment Rating Scores ──
    # Each field stores a number from 1 to 5 selected by the employee
 
    # 1. Punctuality & Attendance
    score_punctuality = models.IntegerField(
        choices=SCORE_CHOICES, null=True, blank=True,
        verbose_name='Punctuality & Attendance'
    )
    # 2. Quality of Work
    score_quality = models.IntegerField(
        choices=SCORE_CHOICES, null=True, blank=True,
        verbose_name='Quality of Work'
    )
    # 3. Teamwork & Collaboration
    score_teamwork = models.IntegerField(
        choices=SCORE_CHOICES, null=True, blank=True,
        verbose_name='Teamwork & Collaboration'
    )
    # 4. Communication Skills
    score_communication = models.IntegerField(
        choices=SCORE_CHOICES, null=True, blank=True,
        verbose_name='Communication Skills'
    )
    # 5. Meeting Deadlines
    score_deadlines = models.IntegerField(
        choices=SCORE_CHOICES, null=True, blank=True,
        verbose_name='Meeting Deadlines'
    )
    # 6. Problem Solving
    score_problem_solving = models.IntegerField(
        choices=SCORE_CHOICES, null=True, blank=True,
        verbose_name='Problem Solving'
    )
    # 7. Initiative & Creativity
    score_initiative = models.IntegerField(
        choices=SCORE_CHOICES, null=True, blank=True,
        verbose_name='Initiative & Creativity'
    )
    # 8. Professionalism
    score_professionalism = models.IntegerField(
        choices=SCORE_CHOICES, null=True, blank=True,
        verbose_name='Professionalism'
    )
    # 9. Adherence to Company Rules
    score_adherence = models.IntegerField(
        choices=SCORE_CHOICES, null=True, blank=True,
        verbose_name='Adherence to Company Rules'
    )
 
    # Optional written comment from the employee
    additional_comments = models.TextField(blank=True)
 
    # ── SECTION 2: Team Lead fills these in ──
    lead_comment = models.TextField(blank=True)
    lead_rating  = models.IntegerField(null=True, blank=True, choices=RATING_CHOICES)
 
    # ── SECTION 3: HR fills these in ──
    hr_comment  = models.TextField(blank=True)
    hr_decision = models.CharField(max_length=100, blank=True)
 
    # ── Timestamps ──
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)
    submitted_to_lead_at = models.DateTimeField(null=True, blank=True)
    submitted_to_hr_at   = models.DateTimeField(null=True, blank=True)
    reviewed_at          = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        ordering = ['-created_at']
 
    def __str__(self):
        name = self.employee_name or (
            self.employee.get_full_name() if self.employee else 'Unknown'
        )
        return f"{name} — {self.period}"
 
    def submit_to_hr(self, lead_user):
        self.status = self.STATUS_PENDING_HR
        self.reviewed_by_lead = lead_user
        self.submitted_to_hr_at = timezone.now()
        self.save()
 
    def mark_reviewed(self, hr_user):
        self.status = self.STATUS_REVIEWED
        self.reviewed_by_hr = hr_user
        self.reviewed_at = timezone.now()
        self.save()
 
    @property
    def status_badge_class(self):
        return {
            self.STATUS_DRAFT:        'badge-draft',
            self.STATUS_PENDING_LEAD: 'badge-lead',
            self.STATUS_PENDING_HR:   'badge-hr',
            self.STATUS_REVIEWED:     'badge-reviewed',
        }.get(self.status, 'badge-draft')
 
    @property
    def display_name(self):
        if self.employee_name:
            return self.employee_name
        if self.employee:
            return self.employee.get_full_name() or self.employee.username
        return 'Unknown'
 
    @property
    def average_score(self):
        """Calculates the average of all 9 self-assessment scores."""
        scores = [
            self.score_punctuality, self.score_quality, self.score_teamwork,
            self.score_communication, self.score_deadlines, self.score_problem_solving,
            self.score_initiative, self.score_professionalism, self.score_adherence,
        ]
        filled = [s for s in scores if s is not None]
        if not filled:
            return None
        return round(sum(filled) / len(filled), 1)