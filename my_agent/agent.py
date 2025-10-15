from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}

root_agent = Agent(
    model=LiteLlm(model='openai/gpt-5-mini-2025-08-07'),
    name='root_agent',
    description='Tells the current time in a specified city.',
    instruction='You are a helpful assistant that tells the current time in cities. Use the "get_current_time" tool for this purpose.',
    tools=[get_current_time],
)
