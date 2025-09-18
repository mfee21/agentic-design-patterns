import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Create a reliable absolute path to a folder named 'mcp_managed_files'
# within the same directory as this agent script.
# This ensures the agent works out-of-the-box for demonstration.
# For production, you would point this to a more persistent and secure location.
TARGET_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_managed_files")

# Ensure the target directory exists before the agent needs it.
os.makedirs(TARGET_FOLDER_PATH, exist_ok=True)

root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='filesystem_assistant_agent',
    instruction=(
        'Help the user manage their files. You can list files, read files, and write files. '
        f'You are operating in the following directory: {TARGET_FOLDER_PATH}'
    ),
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Argument for npx to auto-confirm install
                    "@modelcontextprotocol/server-filesystem",
                    # This MUST be an absolute path to a folder.
                    TARGET_FOLDER_PATH,
                ],
            ),
            # Optional: You can filter which tools from the MCP server are exposed.
            # For example, to only allow reading:
            # tool_filter=['list_directory', 'read_file']
        )
    ],
)

# ---------------------------------------------------------------------------
# ModuleNotFoundError                       Traceback (most recent call last)
# /tmp/ipython-input-1-2988475573.py in <cell line: 0>()
#       1 import os
# ----> 2 from google.adk.agents import LlmAgent
#       3 from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
#       4 
#       5 # Create a reliable absolute path to a folder named 'mcp_managed_files'

# ModuleNotFoundError: No module named 'google.adk'

# ---------------------------------------------------------------------------
# NOTE: If your import is failing due to a missing package, you can
# manually install dependencies using either !pip or !apt.

# To view examples of installing some common dependencies, click the
# "Open Examples" button below.
# ---------------------------------------------------------------------------


connection_params = StdioConnectionParams(
  server_params={
      "command": "python3",
      "args": ["./agent/mcp_server.py"],
      "env": {
        "SERVICE_ACCOUNT_PATH":SERVICE_ACCOUNT_PATH,
        "DRIVE_FOLDER_ID": DRIVE_FOLDER_ID
      }
  }
)


connection_params = StdioConnectionParams(
  server_params={
    "command": "uvx",
    "args": ["mcp-google-sheets@latest"],
    "env": {
      "SERVICE_ACCOUNT_PATH":SERVICE_ACCOUNT_PATH,
      "DRIVE_FOLDER_ID": DRIVE_FOLDER_ID
    }
  }
)