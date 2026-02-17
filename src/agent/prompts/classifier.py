from langchain_core.prompts import ChatPromptTemplate

CLASSIFIER_SYSTEM_PROMPT = """You are an intelligent intent classifier for an AI coding agent named Orbit.
Your job is to analyze the user's latest request and classify it into one of the following categories:

1. "command": The user wants to execute a specific shell command or a simple file operation.
   Examples:
   - "list files in current directory"
   - "create a new folder named test"
   - "read the contents of main.py"
   - "which directory am I in?"
   - "pwd"
   - "git status"

2. "question": The user is asking a general question, seeking an explanation, or chatting. No immediate shell execution is implied.
   Examples:
   - "how does the ls command work?"
   - "what is the best way to structure a python project?"
   - "explain the code in main.py"
   - "hello"
   - "who are you?"

3. "workflow": The user wants to perform a multi-step task or a complex operation that requires planning.
   Examples:
   - "clone the repo, install dependencies, and run the tests"
   - "refactor the auth module to use JWT"
   - "find all unused variables in the src folder and remove them"

4. "confirmation": The user is responding to a confirmation request (e.g., "yes", "no", "proceed").
   Examples:
   - "yes, go ahead"
   - "no, cancel"

Output ONLY the category name (command, question, workflow, confirmation) and nothing else.
"""

classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", CLASSIFIER_SYSTEM_PROMPT),
    ("user", "{input}")
])
