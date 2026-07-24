"""Lazily re-export this level's root node as `root_agent` for `adk web`.

The import is deferred (PEP 562 module `__getattr__`) rather than done at the top
level on purpose: an eager `from .concierge import ...` here would import the module
during package import, and `python -m L3_collaborative.concierge` would then import it a
SECOND time to run it — which makes Python print a RuntimeWarning about
"unpredictable behaviour" as the very first line of every documented command.
Deferring costs nothing: `adk web` still finds `root_agent`, and `python -m` stays quiet.
"""

__all__ = ["root_agent"]


def __getattr__(name):
    if name == "root_agent":
        from .concierge import race_concierge
        return race_concierge
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
