from contextvars import ContextVar

current_tenant: ContextVar[str | None] = ContextVar("current_tenant", default=None)
