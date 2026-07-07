from .deep_research import l4b_workflow as root_agent

# Export the agent so it can be discovered by `adk web`
__all__ = ["root_agent"]
