"""Ask about pace or training. The model decides whether to call the pace tool.

Passthrough: this level is an Agent and already consumes the chat message, so
there is nothing to adapt — it behaves in `adk web` the way it does in the CLI.
It lives here only so `adk web webapps/` shows one clean list.
See _bridge.py for why the other levels need wrapping.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from L0_first_agent.agent import pace_coach as root_agent   # noqa: E402

__all__ = ["root_agent"]
