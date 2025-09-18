from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path.cwd() / ".env", override=True)

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
resp = llm.invoke("Say hi in exactly three words.")
print(resp.content)
