from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import CustomUser, Appraisal
from .forms import PublicAppraisalForm, TeamLeadReviewForm, HRReviewForm


# =============================================================================
# FILE: appraisal/views.py
# WHAT THIS FILE DOES:
#   Each function here handles one URL in the project.
#   When someone visits a URL, Django calls the matching view function.
#   The view function:
#     1. Checks who the user is and whether they are allowed
#     2. Reads or writes data from the database
#     3. Returns a webpage (via render) or sends the user elsewhere (via redirect)
# =============================================================================


# =============================================================================
# SECTION 1 — AUTHENTICATION VIEWS
# These handle logging in and logging out.
# No @login_required here because these pages must be publicly accessible.
# =============================================================================

def login_view(request):
    """
    Shows the login form on GET.
    Processes the login form on POST.
    """
    # If already logged in, skip the login page and go straight to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # authenticate() checks the username and password against the database.
        # Returns the user object if correct, or None if wrong.
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # creates a session so the user stays logged in
            return redirect('dashboard')
        else:
            messages.error(request, 'Incorrect username or password. Please try again.')

    # Show the login page (either first visit or after a failed login)
    return render(request, 'appraisal/login.html')


def logout_view(request):
    """Logs the user out and sends them back to the login page."""
    logout(request)  # clears the session cookie
    return redirect('login')


# =============================================================================
# SECTION 2 — PUBLIC APPRAISAL FORM
# This is the main new feature — employees fill in their appraisal here
# WITHOUT needing to log in. They just enter their name and fill in the form.
# =============================================================================

def public_appraisal(request):
    """
    Shows a blank appraisal form on GET.
    Saves the submitted appraisal on POST and redirects to a thank-you page.
    No login required — anyone with the link can submit.
    """
def public_appraisal(request):
    if request.method == 'POST':
        form = PublicAppraisalForm(request.POST)
        if form.is_valid():
            full_name = (
                form.cleaned_data['first_name'].strip() + ' ' +
                form.cleaned_data['last_name'].strip()
            )
            Appraisal.objects.create(
                employee             = None,
                employee_name        = full_name,
                employee_department  = form.cleaned_data['department'],
                period               = form.cleaned_data['period'],
                # Save all 9 rating scores
                score_punctuality    = form.cleaned_data['score_punctuality'],
                score_quality        = form.cleaned_data['score_quality'],
                score_teamwork       = form.cleaned_data['score_teamwork'],
                score_communication  = form.cleaned_data['score_communication'],
                score_deadlines      = form.cleaned_data['score_deadlines'],
                score_problem_solving = form.cleaned_data['score_problem_solving'],
                score_initiative     = form.cleaned_data['score_initiative'],
                score_professionalism = form.cleaned_data['score_professionalism'],
                score_adherence      = form.cleaned_data['score_adherence'],
                additional_comments  = form.cleaned_data.get('additional_comments', ''),
                status               = Appraisal.STATUS_PENDING_LEAD,
                submitted_to_lead_at = timezone.now(),
            )
            return redirect('public_success')
    else:
        form = PublicAppraisalForm()

    return render(request, 'appraisal/public_form.html', {'form': form})


def public_success(request):
    """Thank-you page shown after a successful public appraisal submission."""
    return render(request, 'appraisal/public_success.html')


# =============================================================================
# SECTION 3 — DASHBOARD ROUTER
# After login, all users go to /dashboard/.
# This view checks their role and sends them to the right dashboard.
# =============================================================================

@login_required  # redirects to the login page if the user is not logged in
def dashboard(request):
    """Sends each role to their own dashboard automatically."""
    user = request.user
    if user.is_employee:
        return redirect('employee_dashboard')
    elif user.is_team_lead:
        return redirect('lead_dashboard')
    elif user.is_hr:
        return redirect('hr_dashboard')
    # Fallback — should not normally reach here
    return redirect('login')


# =============================================================================
# SECTION 4 — TEAM LEAD VIEWS
# The lead can see all appraisals from their team members,
# write a comment and rating, then submit to HR.
# =============================================================================

@login_required
def lead_dashboard(request):
    """Shows the team lead their pending and completed reviews."""

    # Role guard — if a non-lead somehow reaches this URL, send them away
    if not request.user.is_team_lead:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    # Find all employees whose team_lead field points to this lead
    team_members = CustomUser.objects.filter(team_lead=request.user)

    # Get appraisals from those employees that are waiting for lead review
    pending = Appraisal.objects.filter(
        employee__in=team_members,
        status=Appraisal.STATUS_PENDING_LEAD
    )

    # Also get ALL public submissions (employee=None) waiting for lead review
    public_pending = Appraisal.objects.filter(
        employee=None,
        status=Appraisal.STATUS_PENDING_LEAD
    )

    # Combine both querysets so the lead sees everything
    all_pending = (pending | public_pending).distinct()

    # All appraisals ever reviewed by this lead (for history table)
    all_appraisals = Appraisal.objects.filter(reviewed_by_lead=request.user)

    context = {
        'pending':       all_pending,
        'all_appraisals': all_appraisals,
        'pending_count': all_pending.count(),
        'team_count':    team_members.count(),
    }
    return render(request, 'appraisal/lead_dashboard.html', context)


@login_required
def lead_review(request, pk):
    """
    Shows the employee's appraisal alongside a form for the lead to write
    their comment and rating, then submit to HR.
    pk = the primary key (ID number) of the appraisal in the database.
    """
    if not request.user.is_team_lead:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    # get_object_or_404 fetches the appraisal by its ID.
    # If no appraisal with that ID exists, it shows a 404 error page instead of crashing.
    appraisal = get_object_or_404(Appraisal, pk=pk)

    # Only allow the lead to review appraisals that are actually waiting for them
    if appraisal.status != Appraisal.STATUS_PENDING_LEAD:
        messages.warning(request, 'This appraisal is not currently waiting for your review.')
        return redirect('lead_dashboard')

    if request.method == 'POST':
        # instance=appraisal tells Django to UPDATE this existing record, not create a new one
        form = TeamLeadReviewForm(request.POST, instance=appraisal)
        if form.is_valid():
            # commit=False gives us the object without saving yet,
            # so we can call submit_to_hr() which handles the save
            appraisal = form.save(commit=False)
            appraisal.submit_to_hr(request.user)  # saves + advances status to pending_hr
            messages.success(request, f'Review for {appraisal.display_name} submitted to HR.')
            return redirect('lead_dashboard')
    else:
        form = TeamLeadReviewForm(instance=appraisal)

    return render(request, 'appraisal/lead_review.html', {
        'form': form,
        'appraisal': appraisal,
    })


@login_required
def lead_appraisal_detail(request, pk):
    """Read-only view of an appraisal for the team lead."""
    if not request.user.is_team_lead:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    appraisal = get_object_or_404(Appraisal, pk=pk)
    # 'viewer' tells the shared detail template which sections to show
    return render(request, 'appraisal/appraisal_detail.html', {
        'appraisal': appraisal,
        'viewer': 'lead',
    })


# =============================================================================
# SECTION 5 — HR VIEWS
# HR can see ALL appraisals across the whole organisation,
# filter/search them, write final comments, and mark them as reviewed.
# =============================================================================

@login_required
def hr_dashboard(request):
    """Shows HR all appraisals with filtering and search."""
    if not request.user.is_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    # Read filter values from the URL query string
    # e.g. /hr/?status=pending_hr&search=Joseph
    status_filter = request.GET.get('status', '')
    search        = request.GET.get('search', '')

    # select_related fetches related user data in ONE database query instead of many.
    # Without it Django would make a separate query for every row in the table.
    appraisals = Appraisal.objects.select_related('employee', 'reviewed_by_lead')

    # Apply the status filter if one was chosen
    if status_filter:
        appraisals = appraisals.filter(status=status_filter)

    # Apply the search filter if text was entered
    if search:
        # Q objects let us use OR conditions in Django queries.
        # icontains means case-insensitive search (finds 'joseph', 'Joseph', 'JOSEPH')
        appraisals = appraisals.filter(
            Q(employee_name__icontains=search) |
            Q(employee__first_name__icontains=search) |
            Q(employee__last_name__icontains=search) |
            Q(employee__username__icontains=search) |
            Q(period__icontains=search)
        )

    context = {
        'appraisals':     appraisals,
        'status_filter':  status_filter,  # keeps the dropdown on the selected option
        'search':         search,         # keeps the search box filled in
        'total':          Appraisal.objects.count(),
        'pending_hr':     Appraisal.objects.filter(status=Appraisal.STATUS_PENDING_HR).count(),
        'reviewed':       Appraisal.objects.filter(status=Appraisal.STATUS_REVIEWED).count(),
        'status_choices': Appraisal.STATUS_CHOICES,  # populates the filter dropdown
    }
    return render(request, 'appraisal/hr_dashboard.html', context)


@login_required
def hr_review(request, pk):
    """HR writes their final comment and decision, then marks the appraisal as reviewed."""
    if not request.user.is_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    appraisal = get_object_or_404(Appraisal, pk=pk)

    if request.method == 'POST':
        form = HRReviewForm(request.POST, instance=appraisal)
        if form.is_valid():
            appraisal = form.save(commit=False)
            appraisal.mark_reviewed(request.user)  # saves + sets status to reviewed
            messages.success(request, f'Appraisal for {appraisal.display_name} has been finalised.')
            return redirect('hr_dashboard')
    else:
        form = HRReviewForm(instance=appraisal)

    return render(request, 'appraisal/hr_review.html', {
        'form': form,
        'appraisal': appraisal,
    })


@login_required
def hr_appraisal_detail(request, pk):
    """Read-only view of any appraisal for HR."""
    if not request.user.is_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    appraisal = get_object_or_404(Appraisal, pk=pk)
    return render(request, 'appraisal/appraisal_detail.html', {
        'appraisal': appraisal,
        'viewer': 'hr',
    })
