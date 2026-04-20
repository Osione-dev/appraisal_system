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

    # ── Rating scale used by the Team Lead ──
    RATING_CHOICES = [
        (1, '1 - Needs Improvement'),
        (2, '2 - Below Expectations'),
        (3, '3 - Meets Expectations'),
        (4, '4 - Exceeds Expectations'),
        (5, '5 - Outstanding'),
    ]

    # ── Who is involved ──
    # employee: links to a CustomUser account (nullable for public submissions)
    # null=True, blank=True → allows public submissions where there is no user account
    # CASCADE → if the employee's account is deleted, their appraisals are deleted too
    employee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='appraisals',
        null=True,
        blank=True,
        limit_choices_to={'role': CustomUser.ROLE_EMPLOYEE}
    )

    # These two fields store the name and department for PUBLIC submissions
    # (employees who fill in the form without logging in)
    employee_name       = models.CharField(max_length=200, blank=True)
    employee_department = models.CharField(max_length=100, blank=True)

    # reviewed_by_lead: filled in automatically when the lead submits their review
    # SET_NULL → if the lead account is deleted, this field becomes null (appraisal stays)
    reviewed_by_lead = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lead_reviews',
        limit_choices_to={'role': CustomUser.ROLE_TEAM_LEAD}
    )

    # reviewed_by_hr: filled in automatically when HR finalises the appraisal
    reviewed_by_hr = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hr_reviews',
        limit_choices_to={'role': CustomUser.ROLE_HR}
    )

    # ── General info ──
    period = models.CharField(max_length=100)  # e.g. "Q1 2025" or "Annual 2025"
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_LEAD  # public submissions go straight to lead queue
    )

    # ── SECTION 1: Employee fills these in ──
    self_summary      = models.TextField()
    achievements      = models.TextField()
    challenges        = models.TextField()
    goals_next_period = models.TextField()
    training_needs    = models.TextField(blank=True)    # optional
    additional_comments = models.TextField(blank=True)  # optional

    # ── SECTION 2: Team Lead fills these in ──
    lead_comment = models.TextField(blank=True)
    lead_rating  = models.IntegerField(null=True, blank=True, choices=RATING_CHOICES)

    # ── SECTION 3: HR fills these in ──
    hr_comment  = models.TextField(blank=True)
    hr_decision = models.CharField(max_length=100, blank=True)

    # ── Timestamps ──
    # auto_now_add → set ONCE when the record is first created, never changes
    # auto_now     → updated EVERY TIME the record is saved
    # The others are set manually inside the workflow methods below
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)
    submitted_to_lead_at = models.DateTimeField(null=True, blank=True)
    submitted_to_hr_at  = models.DateTimeField(null=True, blank=True)
    reviewed_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']  # newest appraisals appear first

    def __str__(self):
        # Show employee name — use the name field for public submissions
        name = self.employee_name or (
            self.employee.get_full_name() if self.employee else 'Unknown'
        )
        return f"{name} — {self.period}"

    # ── Workflow methods ──
    # These move the appraisal through the pipeline one step at a time.

    def submit_to_hr(self, lead_user):
        """Called when the Team Lead submits their review."""
        self.status = self.STATUS_PENDING_HR
        self.reviewed_by_lead = lead_user
        self.submitted_to_hr_at = timezone.now()
        self.save()

    def mark_reviewed(self, hr_user):
        """Called when HR finalises the appraisal."""
        self.status = self.STATUS_REVIEWED
        self.reviewed_by_hr = hr_user
        self.reviewed_at = timezone.now()
        self.save()

    @property
    def status_badge_class(self):
        """Returns a CSS class name based on the current status, used in templates."""
        return {
            self.STATUS_DRAFT:        'badge-draft',
            self.STATUS_PENDING_LEAD: 'badge-lead',
            self.STATUS_PENDING_HR:   'badge-hr',
            self.STATUS_REVIEWED:     'badge-reviewed',
        }.get(self.status, 'badge-draft')

    @property
    def display_name(self):
        """Returns the employee's name whether they logged in or submitted publicly."""
        if self.employee_name:
            return self.employee_name
        if self.employee:
            return self.employee.get_full_name() or self.employee.username
        return 'Unknown'
