# hopper_agent/agent.py
from google.adk.agents import Agent
from google.adk.sessions import Session
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.interview_prep_agent.agent import interview_prep_agent
from .sub_agents.job_research_agent.agent import job_research_agent
from .sub_agents.package_agent.agent import resume_agent


# Wrap subagents as tools
interview_prep_tool = AgentTool(interview_prep_agent)
job_research_tool = AgentTool(job_research_agent)
application_materials_tool = AgentTool(resume_agent)

application_agent = Agent(
    name="application_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are Hopper, the orchestrator for a multi-agent career-coaching system. "
        "Your job is to understand the user's request and delegate to specialized agents "
        "via the tools you have available.\n\n"

        "Routing guidance:\n"
        "- If the user asks for interview prep, sample questions, or any artifact to help with an interview, use the interview_prep_tool.\n"
        "- If the user asks to research a company, job role/function, or LinkedIn connections, use the job_research_tool.\n"
        "- If the user asks to create a tailored resume, cover letter, application email, or cold outreach email, use the application_materials_tool.\n\n"

        "Be transparent about what's available. Do not invent capabilities; if a subagent "
        "says 'That functionality is not yet built.', just return that to the user, prefixed with 'Application Agent: '."
    ),
    tools=[
        interview_prep_tool,
        job_research_tool,
        application_materials_tool,
    ],
)


def main():
    session = Session()

    print("Hopper orchestrator. Talk to your career copilot. Ctrl+C to exit.")
    while True:
        user_input = input("\nYou: ")
        result = application_agent.run(session=session, user_input=user_input)
        print("\nApplication Agent:", result.text)
