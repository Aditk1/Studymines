"""
src/utils/error_handler.py — Premium Explainable Error System.
Transforms standard Python tracebacks into human-readable causes and solutions.
"""
import traceback
import sys
import os
import functools
import asyncio
from typing import Any, Callable, Optional, TypeVar, Union

T = TypeVar("T")

# ANSI escape codes for premium CLI aesthetics
class Colors:
    """Define the Colors data structure or service used by this module."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GRAY = '\033[90m'

def explain_error(exc: Exception, context: str = "", use_llm: bool = False):
    """
    Prints a detailed, explainable error report to the command prompt.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    print(f"\n{Colors.FAIL}{Colors.BOLD}=== EXPLORA ERROR SYSTEM ==={Colors.ENDC}")
    
    if context:
        print(f"{Colors.CYAN}{Colors.BOLD}Context:{Colors.ENDC} {context}")
    
    print(f"{Colors.FAIL}{Colors.BOLD}Type:   {Colors.ENDC} {exc_type.__name__ if exc_type else 'Unknown'}")
    print(f"{Colors.FAIL}{Colors.BOLD}Message:{Colors.ENDC} {str(exc_value)}")
    
    # 1. Deterministic categorization
    cause, action = categorize_error(exc)
    
    print(f"\n{Colors.WARNING}{Colors.BOLD}Possible Cause:{Colors.ENDC}\n{cause}")
    print(f"\n{Colors.GREEN}{Colors.BOLD}Suggested Action:{Colors.ENDC}\n{action}")
    
    # 2. Optional LLM Explanation (Premium feature)
    if use_llm:
        print(f"\n{Colors.CYAN}{Colors.BOLD}AI Analysis of Issue...{Colors.ENDC}")
        ai_explanation = try_ai_explanation(exc, context)
        if ai_explanation:
            print(f"{Colors.BOLD}AI Insight:{Colors.ENDC}\n{ai_explanation}")

    # 3. Clean Traceback
    print(f"\n{Colors.BLUE}{Colors.BOLD}Traceback Summary (Recent Frames):{Colors.ENDC}")
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    
    # Print max 3 relevant frames
    for line in tb_lines[-3:]:
        print(f"  {Colors.GRAY}{line.strip()}{Colors.ENDC}")
    
    print(f"{Colors.FAIL}{Colors.BOLD}-----------------------------------{Colors.ENDC}\n")

def categorize_error(exc: Exception) -> tuple[str, str]:
    """
    Returns (Possible Cause, Suggested Action) based on exception type/message.
    """
    msg = str(exc).lower()
    
    if isinstance(exc, FileNotFoundError) or "no such file" in msg:
        return (
            "The system tried to access a file or directory that doesn't exist at the specified path.",
            "Double-check the file path. Ensure that required data directories (e.g., data/uploads, outputs/logs) exist. "
            "If you are running a script, check the '--path' arguments."
        )
    
    if "api_key" in msg or "authentication" in msg or "unauthorized" in msg or "401" in msg:
        return (
            "There seems to be an authentication issue with an LLM provider (Groq, Gemini, OpenAI, etc.).",
            "Verify your '.env' file. Ensure variables like 'GROQ_API_KEY' or 'GOOGLE_API_KEY' are correctly set and valid."
        )
        
    if "connection" in msg or "timeout" in msg or "refused" in msg:
        return (
            "The network request failed or timed out. This often happens if the provider is down or your internet is unstable.",
            "Check your internet connection. If using Ollama, ensure the local server is running (`ollama serve`)."
        )
        
    if "memory" in msg or "cuda" in msg or "alloc" in msg:
        return (
            "System is out of memory (RAM or GPU VRAM).",
            "Try closing other heavy applications. If running local LLMs/Embeddings, try a smaller model (e.g., 'llama3.2:1b')."
        )

    if "table" in msg or "column" in msg or "sqlite" in msg or "database" in msg or "sqlalchemy" in msg:
        return (
            "A database error occurred. This might be due to a schema mismatch, a missing table, or a unique constraint violation.",
            "Check if 'master_edurag.db' exists. You might need to re-run your database initialization script."
        )
    
    if "module" in msg and "not found" in msg:
        return (
            "A required Python package is missing.",
            "Run `pip install -r requirements.txt` to ensure all dependencies are installed."
        )

    # Generic fallback
    return (
        "An unhandled execution error occurred.",
        "Inspect the traceback summary below for the specific line number where the fault occurs."
    )

def try_ai_explanation(exc: Exception, context: str) -> Optional[str]:
    """
    Attempts to use the project LLM to explain the error.
    """
    from src.utils.llm_client import LLMClient
    from src.utils.config import load_config
    
    try:
        # Load config and init client (sync)
        config = load_config()
        client = LLMClient(config.llm)
        
        prompt = f"""Expert Python Developer: Explain this error in a way a student can understand.
Context: {context}
Error Type: {type(exc).__name__}
Error Message: {str(exc)}

Tell them EXACTLY what likely went wrong and one specific step to fix it. Keep it under 3 sentences.
"""
        response = client.generate_sync(prompt, system="You are an expert EduRAG debugger.")
        if response.content and "[LLM ERROR]" not in response.content:
            return response.content
    except Exception:
        pass # Fail silently
    return None

def wrap_explain(context: str = "", use_llm: bool = True):
    """
    Decorator to wrap functions with explainable error handling.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ctx = context or f"Executing '{func.__name__}'"
                explain_error(e, context=ctx, use_llm=use_llm)
                raise # Re-raise to let the program flow handle it if needed
        return wrapper
    return decorator

def wrap_explain_async(context: str = "", use_llm: bool = True):
    """
    Decorator to wrap async functions with explainable error handling.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                ctx = context or f"Executing async '{func.__name__}'"
                explain_error(e, context=ctx, use_llm=use_llm)
                raise
        return wrapper
    return decorator
