from django.urls import path
from . import views

# =============================================================================
# FILE: appraisal/urls.py
# WHAT THIS FILE DOES:
#   Maps every URL in the project to the view function that handles it.
#   When a user visits a URL, Django looks down this list and calls
#   the matching view function.
#
# URL STRUCTURE:
#   /                  → login page
#   /submit/           → public appraisal form (no login needed)
#   /submit/done/      → thank you page after submission
#   /dashboard/        → routes to the right dashboard based on role
#   /lead/             → team lead dashboard
#   /hr/               → hr dashboard
#   /admin/            → Django admin panel (defined in project urls.py)
# =============================================================================

urlpatterns = [

    # ── Public pages (no login required) ──
    path('',             views.login_view,      name='login'),
    path('login/',       views.login_view,      name='login'),
    path('logout/',      views.logout_view,     name='logout'),
    path('submit/',      views.public_appraisal, name='public_appraisal'),
    path('submit/done/', views.public_success,  name='public_success'),

    # ── Dashboard router ──
    path('dashboard/', views.dashboard, name='dashboard'),

    # ── Team Lead pages ──
    path('lead/',                              views.lead_dashboard,        name='lead_dashboard'),
    path('lead/appraisal/<int:pk>/review/',   views.lead_review,           name='lead_review'),
    path('lead/appraisal/<int:pk>/',          views.lead_appraisal_detail, name='lead_appraisal_detail'),

    # ── HR pages ──
    path('hr/',                            views.hr_dashboard,        name='hr_dashboard'),
    path('hr/appraisal/<int:pk>/review/',  views.hr_review,           name='hr_review'),
    path('hr/appraisal/<int:pk>/',         views.hr_appraisal_detail, name='hr_appraisal_detail'),

    path('submit/', views.public_appraisal, name='public_appraisal'),
    path('submit/done/', views.public_success, name='public_success'),
]
