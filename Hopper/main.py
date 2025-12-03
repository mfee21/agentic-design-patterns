import asyncio

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from utils import add_user_query_to_history

load_dotenv()

# ===== PART 1: Initialize In-Memory Session Service =====
# Using in-memory storage for this example (non-persistent)
session_service = InMemorySessionService()


# ===== PART 2: Define Initial State =====
# This will be used when creating a new session
initial_state = {
    "user_name": "Matthew Fee",
}


async def main_async():
    # Setup constants
    APP_NAME = "Hopper Career Assistant"
    USER_ID = "matt_fee"

    # ===== PART 3: Session Creation =====
    # Create a new session with initial state
    new_session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state=initial_state,
    )
    SESSION_ID = new_session.id
    print(f"Created new session: {SESSION_ID}")

    # ===== PART 4: Agent Runner Setup =====
    # Create a runner with the main customer service agent
    from hopper_agent.agent import hopper_agent

    runner = Runner(
        agent=hopper_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # ===== PART 5: Interactive Conversation Loop =====
    print("\nWelcome to Hopper Career Assistant!")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Ending conversation. Goodbye!")
            break
        await add_user_query_to_history(
            session_service, APP_NAME, USER_ID, SESSION_ID, user_input
        )
        message = types.Content(role="user", parts=[types.Part(text=user_input)])
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=message,
        ):
            if (
                hasattr(event, "content")
                and event.content
                and hasattr(event.content.parts[0], "text")
            ):
                print("\nHopper:", event.content.parts[0].text)

    # ===== PART 6: State Examination =====
    # Show final session state
    final_session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    print("\nFinal Session State:")
    for key, value in final_session.state.items():
        print(f"{key}: {value}")


def main():
    """Entry point for the application."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()