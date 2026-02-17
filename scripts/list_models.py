import google.genai
import os
from src.config import settings

# Ensure API key is set
if not settings.GOOGLE_API_KEY:
    print("GOOGLE_API_KEY not set in environment or config.")
    exit(1)

try:
    # Initialize client - guessing client initialization based on typical patterns if docs are not available
    # The new google-genai library usage:
    # client = google.genai.Client(api_key=...)
    client = google.genai.Client(api_key=settings.GOOGLE_API_KEY)
    
    # List models
    print("Listing models...")
    # Trying models.list()
    if hasattr(client, 'models') and hasattr(client.models, 'list'):
        models = client.models.list()
        for i, model in enumerate(models):
            print(f"{i}: {model.name}")
    else:
        print("Could not find client.models.list method.")
        print(dir(client))

except Exception as e:
    print(f"Error listing models: {e}")
