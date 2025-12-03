from google.adk.agents import Agent

interview_prep_agent = Agent(
    name="interview_prep_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a stub for a future Interview Prep Agent. "
        "For every request, respond EXACTLY with: "
        "'Interview Prep Agent functionality is not yet built.'"
    ),
)
# ...existing code...
