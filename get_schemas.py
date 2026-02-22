import sys
import os

sys.path.append(os.getcwd())

from src.tools.registry import get_tool_registry
import json

print(json.dumps(get_tool_registry().get_all_schemas(), indent=2))
