from google.adk.agents import Agent

job_research_agent = Agent(
    name="job_research_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a stub for a future Job Research Agent. "
        "For every request, respond EXACTLY with: "
        "'Job Research Agent functionality is not yet built.'"
    ),
)
# ...existing code...
