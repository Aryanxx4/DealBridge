"""Feature routers, registered as each gate lands."""

from app.api import admin_dashboard, analysis, assessments, chat, jobs, knowledge_admin, tickets_admin

ROUTERS = [
    jobs.router,
    knowledge_admin.router,
    chat.router,
    tickets_admin.router,
    admin_dashboard.router,
    assessments.router,
    analysis.router,
]
