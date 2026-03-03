#!/usr/bin/env python3
"""
Script to update planner.py with memory_context support.
This script adds memory_context parameter to _create_simple_plan
and updates system_prompt to include memory context.
"""

import re

# Read the file
with open('src/agent/nodes/planner.py', 'r') as f:
    content = f.read()

# Replace _create_simple_plan function signature
old_signature = '''async def _create_simple_plan(self, user_request: str, max_steps: int = 3) -> Plan:'''

# Update signature with memory_context parameter
new_signature = '''async def _create_simple_plan(self, state: AgentState, user_request: str, max_steps: int = 3, memory_context: str = "") -> Plan:'''

# Replace in content
if old_signature in content:
    # Find and replace the function
    pattern = rf'(async def _create_simple_plan\([^:)]+) -> Plan:(?s*?)".format(re.escape(re.escape('Plan:')))
    if not pattern:
        print("ERROR: Could not find _create_simple_plan function signature")
        exit(1)

    # Replace the signature line
    new_func = pattern.sub(r'\1', f'''async def _create_simple_plan(self, state: AgentState, user_request: str, max_steps: int = 3, memory_context: str = "") -> Plan:''')

    # Now update the system_prompt f-string to include memory_context
    # Look for the system_prompt line after the function signature
    system_prompt_pattern = r'(system_prompt = f"""You are an AI assistant.*?User request: "\{user_request\}"""\n)(.*?)Available tools:\n\{tools_description\}'

    def add_memory_context(match):
        """Add memory_context to the system_prompt f-string."""
        # Extract the closing """ and Available tools: line
        before_available = match.group(1)
        after_available = match.group(2)
        closing_quote = match.group(3)
        tools_section = match.group(2)

        # Build the new memory context section
        memory_section = f'''

Memory Context:
{memory_context}

'''

        # Reconstruct with memory context section inserted
        new_section = f'''{before_available}
{memory_section}
{closing_quote}
{after_available}'''

    # Find and replace the system_prompt line
    pattern = r'(system_prompt = f"""You are an AI assistant. Create a simple execution plan for the user\\'s request\.
User request: "\{user_request\}""

Available tools:
\{tools_description\}
IMPORTANT: Only use tool_name values from this exact list: \{tool_names\}
Output a JSON object with this structure:'''

    if re.search(pattern, content):
        new_content = re.sub(pattern, r'\1', f'''system_prompt = f"""You are an AI assistant. Create a simple execution plan for the user\\'s request.
User request: "{user_request}"

Memory Context:
{memory_context}

Available tools:
{tools_description}
IMPORTANT: Only use tool_name values from this exact list: {tool_names}
Output a JSON object with this structure:''')

        # Write back
        with open('src/agent/nodes/planner.py', 'w') as f:
            f.write(new_content)

        print("SUCCESS: Updated planner.py with memory_context support")
    else:
        print("ERROR: Could not find system_prompt pattern to update")
        exit(1)
