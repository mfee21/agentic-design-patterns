from google.adk.agents import Agent

career_coach_agent = Agent(
    name="career_coach_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a stub for a future Career Coach Agent. "
        "For every request, respond EXACTLY with: "
        "'Career Coach Agent: That functionality is not yet built.'"
    ),
)
