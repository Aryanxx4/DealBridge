"""Feature routers, registered as each gate lands."""

from app.api import chat, jobs, knowledge_admin

ROUTERS = [jobs.router, knowledge_admin.router, chat.router]
