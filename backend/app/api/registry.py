"""Feature routers, registered as each gate lands."""

from app.api import admin_dashboard, analysis, assessments, chat, jobs, knowledge_admin, p1, sharing, tickets_admin

ROUTERS = [
    jobs.router,
    knowledge_admin.router,
    chat.router,
    tickets_admin.router,
    admin_dashboard.router,
    assessments.router,
    analysis.router,
    sharing.router,
    p1.router,
]
