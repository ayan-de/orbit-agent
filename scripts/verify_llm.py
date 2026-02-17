import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.llm.factory import llm_factory
from src.config import settings

# Mock keys if not set for testing initialization
# Note: We are modifying the settings instance directly for this test run
original_openai_key = settings.OPENAI_API_KEY
original_anthropic_key = settings.ANTHROPIC_API_KEY
original_google_key = settings.GOOGLE_API_KEY

if not settings.OPENAI_API_KEY:
    settings.OPENAI_API_KEY = "sk-test-key"
if not settings.ANTHROPIC_API_KEY:
    settings.ANTHROPIC_API_KEY = "sk-ant-test-key"
if not settings.GOOGLE_API_KEY:
    settings.GOOGLE_API_KEY = "AIza-test-key"

print("--- Testing LLM Factory ---")

print("1. Testing OpenAI initialization...")
try:
    llm = llm_factory(provider="openai")
    print(f"✅ OpenAI model initialized successfully: {llm.__class__.__name__}")
except Exception as e:
    print(f"❌ Failed to initialize OpenAI model: {e}")

print("\n2. Testing Anthropic initialization...")
try:
    llm = llm_factory(provider="anthropic")
    print(f"✅ Anthropic model initialized successfully: {llm.__class__.__name__}")
except Exception as e:
    print(f"❌ Failed to initialize Anthropic model: {e}")

print("\n3. Testing Gemini initialization...")
try:
    llm = llm_factory(provider="gemini")
    print(f"✅ Gemini model initialized successfully: {llm.__class__.__name__}")
except Exception as e:
    print(f"❌ Failed to initialize Gemini model: {e}")

# Restore original keys (not strictly necessary as this script ends, but good practice)
settings.OPENAI_API_KEY = original_openai_key
settings.ANTHROPIC_API_KEY = original_anthropic_key
settings.GOOGLE_API_KEY = original_google_key
