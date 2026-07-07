# L0 · Your first ADK 2 agent

**The question:** can you get a model to answer, with the minimum ADK moving parts?

**The one idea:** two objects.
- **`Agent`** — the thing that reasons (a Gemini model + an instruction).
- **`Runner`** — the thing that executes an agent inside a session and streams back events.

Everything else in this tutorial is more agents, arranged in more interesting shapes. This is the atom.

## Run it
```bash
python -m L0_first_agent.agent
python -m L0_first_agent.agent "What should I eat the night before a marathon?"
```

## What you'll see
The coach answers your question in a few sentences. That's the whole program — one `Agent`, one `Runner`, one `run_async` loop reading `event`s.

## The shape of the code
```python
pace_coach = Agent(name=..., model="gemini-flash-latest", instruction=...)
runner = Runner(node=pace_coach, session_service=InMemorySessionService(), auto_create_session=True)
async for event in runner.run_async(user_id=..., session_id=..., new_message=Content(...)):
    ...  # events carry the model's text
```

→ **Next:** [L1](../L1_graph_basics/) puts this agent *inside a graph*, with a plain Python function feeding it — your first `Workflow`.
