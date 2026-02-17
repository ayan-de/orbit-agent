import asyncio
import sys
import os

# Set unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.utils.safety import is_safe_command

async def run_safety_test(command: str, expected_safe: bool):
    print(f"\nTesting Command: '{command}'", flush=True)
    try:
        is_safe, reason = await is_safe_command(command)
        
        status = "✅ PASS" if is_safe == expected_safe else "❌ FAIL"
        print(f"{status}: Classified as {'SAFE' if is_safe else 'UNSAFE'} ({reason})", flush=True)
    except Exception as e:
        print(f"❌ ERROR: {e}", flush=True)

async def main():
    print("--- Testing Safety Classifier ---", flush=True)
    
    test_cases = [
        ("ls -la", True),
        ("rm -rf /", False),
    ]
    
    for cmd, expected in test_cases:
        await run_safety_test(cmd, expected)

if __name__ == "__main__":
    asyncio.run(main())
