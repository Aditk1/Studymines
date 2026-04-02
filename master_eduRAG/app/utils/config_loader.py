"""
Unified configuration loader for master_eduRAG.
Provides consistent path resolution and config loading across all modules.
"""

from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """
    Get the project root directory.
    Works from any module location by finding the common ancestor.
    
    Returns:
        Path to project root (directory containing app/, src/, config/)
    """
    # Start from this file's location
    current = Path(__file__).parent
    
    # Go up until we find a directory with app/, src/, and config/ subdirectories
    while current != current.parent:  # Stop at filesystem root
        if (current / "app").exists() and (current / "src").exists() and (current / "config").exists():
            return current
        current = current.parent
    
    # Fallback: return parent of app/ (this should be the project root when called from app/)
    # This handles the case where we start from within app/
    fallback = Path(__file__).parent.parent.parent
    return fallback


def get_config_path(filename: str = "base.yaml") -> Path:
    """
    Get the path to a config file.
    
    Args:
        filename: Config file name (default: base.yaml)
        
    Returns:
        Path object pointing to the config file
    """
    project_root = get_project_root()
    config_file = project_root / "config" / filename
    return config_file


def load_config(filepath: Optional[str] = None):
    """
    Load YAML configuration file.
    Uses the src.utils.config.load_config function if available.
    
    Args:
        filepath: Optional path to config file. If not provided, uses base.yaml
        
    Returns:
        Parsed configuration object
    """
    if not filepath:
        filepath = str(get_config_path())
    
    try:
        from src.utils.config import load_config as src_load_config
        return src_load_config(filepath)
    except ImportError:
        # Fallback if src module not available
        import yaml
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)


__all__ = [
    "get_project_root",
    "get_config_path",
    "load_config",
]
