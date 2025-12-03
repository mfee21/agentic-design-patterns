from google.adk.agents import Agent

resume_agent = Agent(
    name="resume_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a stub for a future Resume Agent. "
        "For every request, respond EXACTLY with: "
        "'Resume Agent functionality is not yet built.'"
    ),
)
# ...existing code...
