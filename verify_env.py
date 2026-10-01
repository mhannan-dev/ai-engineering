import os
import sys
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import litellm
import instructor
import pydantic

def verify_environment():
    load_dotenv()
    print("--- Verifying AI Engineering Environment Setup ---")
    print(f"[✓] Pydantic Version: {pydantic.__version__}")
    try:
        import importlib.metadata
        litellm_ver = importlib.metadata.version("litellm")
    except Exception:
        litellm_ver = getattr(litellm, "__version__", "installed")
    print(f"[✓] LiteLLM Version: {litellm_ver}")
    print(f"[✓] Instructor Version: {instructor.__version__}")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and not api_key.startswith("your-"):
        print("[✓] API Key detected successfully in .env file.")
    else:
        print("[!] Warning: OPENAI_API_KEY is missing or unconfigured in .env file.")
        
    print("--- Environment Readiness Verification Complete ---")

if __name__ == "__main__":
    verify_environment()