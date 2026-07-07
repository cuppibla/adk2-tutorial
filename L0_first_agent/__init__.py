from .agent import pace_coach as root_agent

# Export the agent so it can be discovered by `adk web`
__all__ = ["root_agent"]
