# hopper_agent/agent.py
from google.adk.agents import Agent
from google.adk.sessions import Session
from google.adk.tools.agent_tool import AgentTool

from sub_agents.job_search_agent import job_search_agent
from sub_agents.career_coach_agent import career_coach_agent
from sub_agents.application_agent.sub_agents.resume_agent import resume_agent
from sub_agents.application_agent.sub_agents.job_research_agent import job_research_agent
from sub_agents.application_agent.sub_agents.interview_prep_agent import interview_prep_agent


# Wrap subagents as tools
job_search_tool = AgentTool(job_search_agent)
resume_tool = AgentTool(resume_agent)
career_coach_tool = AgentTool(career_coach_agent)
job_research_tool = AgentTool(job_research_agent)
interview_prep_tool = AgentTool(interview_prep_agent)


hopper_agent = Agent(
    name="hopper_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are Hopper, the orchestrator for a multi-agent career-coaching system. "
        "Your job is to understand the user's request and delegate to specialized agents "
        "via the tools you have available.\n\n"
        "Available functionality (as of now):\n"
        "- Job Search: You can scrape jobs from LinkedIn using built scraper tools, and extract jobs from your Gmail job alert emails (currently LinkedIn alerts; more sources coming soon). Use the job_search_tool.\n\n"
        "Routing guidance:\n"
        "If a user request matches anything in Coming soon, respond exactly with: 'That functionality is not yet built.' "
        "Be transparent about what's available. Do not invent capabilities."
    ),
    tools=[
        job_search_tool,
        resume_tool,
        career_coach_tool,
        job_research_tool,
        interview_prep_tool,
    ],
)


def main():
    session = Session()

    actions = [
        "Run job search (scrape jobs and save to DB)",
        "Extract LinkedIn jobs from Gmail and save to DB",
        "Extract BuiltIn jobs from Gmail and save to DB",
        "Quit"
    ]

    print("Welcome to Hopper Career Assistant!")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("\nHopper: Quick Menu:")
    for idx, action in enumerate(actions, 1):
        print(f"  {idx}. {action}")
    while True:
        choice = input("Select an action by number: ").strip()
        if choice == "1":
            result = hopper_agent.run(session=session, user_input="job search")
        elif choice == "2":
            result = hopper_agent.run(session=session, user_input="extract linkedin jobs from gmail")
        elif choice == "3":
            result = hopper_agent.run(session=session, user_input="extract builtin jobs from gmail")
        elif choice == "4" or choice.lower() in ["exit", "quit"]:
            print("Hopper: Goodbye!")
            break
        else:
            print("Hopper: Invalid selection. Please try again.")
            print("\nHopper: Quick Menu:")
            for idx, action in enumerate(actions, 1):
                print(f"  {idx}. {action}")
            continue
        # Debug trace
        agent_name = getattr(result, 'agent_name', "")
        text = result.text if result.text is not None else ""
        if agent_name:
            if text and text.strip().lower() != "none":
                print(f"\nHopper: {agent_name.replace('_', ' ').title()} {text}")
            else:
                print(f"\nHopper: {agent_name.replace('_', ' ').title()}")
            print("\nHopper: Quick Menu:")
            for idx, action in enumerate(actions, 1):
                print(f"  {idx}. {action}")
            continue
        print("\nHopper:")
        print("\nHopper: Quick Menu:")
        for idx, action in enumerate(actions, 1):
            print(f"  {idx}. {action}")
