"""
Utility helpers for robust LLM JSON parsing and response normalization.
"""

import json
import re
import time
import functools
from typing import Dict, Any, Callable
from google.api_core import exceptions

def clean_json_response(text: str):
    """
    Cleans LLM response text by removing markdown code blocks 
    and other non-JSON characters before parsing.
    Handles both JSON objects ({...}) and JSON arrays ([...]).
    """
    # Remove markdown code blocks if present
    # Matches ```json ... ``` or ``` ... ```
    json_match = re.search(r'```(?:json)?\s*([\[{].*[\]}])\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        # Detect whether the response is an array or object
        stripped = text.strip()
        first_bracket = stripped.find('[')
        first_brace = stripped.find('{')
        
        # Determine which comes first — array or object
        if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
            # It's a JSON array
            last_bracket = stripped.rfind(']')
            if last_bracket != -1:
                text = stripped[first_bracket:last_bracket + 1]
        elif first_brace != -1:
            # It's a JSON object
            last_brace = stripped.rfind('}')
            if last_brace != -1:
                text = stripped[first_brace:last_brace + 1]
    
    try:
        return json.loads(text.strip())
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        raise ValueError(f"Invalid JSON response from model: {str(e)}")

def retry_with_backoff(retries: int = 5, backoff_in_seconds: int = 2):
    """Decorator to retry a function on 429 (Quota Exceeded) or 500 (Internal Error) errors."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except (exceptions.ResourceExhausted, exceptions.InternalServerError) as e:
                    if attempt < retries:
                        # Extra wait for 429 to clear
                        actual_backoff = backoff_in_seconds if not isinstance(e, exceptions.ResourceExhausted) else backoff_in_seconds * 3
                        sleep_time = (actual_backoff * (2 ** attempt))
                        print(f"⚠ API Error ({type(e).__name__}). Retrying attempt {attempt + 1}/{retries} in {sleep_time}s...")
                        time.sleep(sleep_time)
                        attempt += 1
                    else:
                        raise e
                except Exception as e:
                    # Fallback for other exception types that might contain 429/quota
                    err_msg = str(e)
                    if ("429" in err_msg or "Quota" in err_msg) and attempt < retries:
                        sleep_time = (backoff_in_seconds * 5 * (2 ** attempt))
                        print(f"⚠ Quota Error (429). Retrying attempt {attempt + 1}/{retries} in {sleep_time}s...")
                        time.sleep(sleep_time)
                        attempt += 1
                    else:
                        raise e
        return wrapper
    return decorator
