from google.adk.agents import Agent

package_agent = Agent(
    name="package_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a stub for a future Package Agent. "
        "For every request, respond EXACTLY with: "
        "'Package Agent functionality is not yet built.'"
    ),
)
# ...existing code...
