"""Request-scoped workspace identity; propagated to FastAPI worker threads."""

from contextvars import ContextVar

workspace_id = ContextVar("workspace_id", default="local")
