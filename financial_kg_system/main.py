"""
Configuration and Entry Point for Financial Knowledge Graph System
"""

import os
from typing import Dict, Any
import yaml
from pathlib import Path
from api import app  # Import the API app
import uvicorn


# Default configuration settings
DEFAULT_CONFIG = {
    # Database settings
    "database": {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "password"),
        "encrypted": os.getenv("NEO4J_ENCRYPTED", "false").lower() == "true"
    },
    
    # Cache settings
    "cache": {
        "redis_host": os.getenv("REDIS_HOST", "localhost"),
        "redis_port": int(os.getenv("REDIS_PORT", "6379")),
        "redis_password": os.getenv("REDIS_PASSWORD", None),
        "graph_cache_ttl": int(os.getenv("GRAPH_CACHE_TTL", "3600")),  # 1 hour
        "value_cache_ttl": int(os.getenv("VALUE_CACHE_TTL", "600"))   # 10 minutes
    },
    
    # API settings
    "api": {
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", "8000")),
        "reload": os.getenv("API_RELOAD", "true").lower() == "true",
        "workers": int(os.getenv("API_WORKERS", "1"))
    },
    
    # Calculation settings
    "calculation": {
        "max_concurrent_calculations": int(os.getenv("MAX_CONCURRENT_CALCULATIONS", "5")),
        "enable_caching": os.getenv("ENABLE_CACHING", "true").lower() == "true",
        "max_memory_mb": int(os.getenv("MAX_MEMORY_MB", "2048")),
        "enable_audit_trail": os.getenv("ENABLE_AUDIT_TRAIL", "true").lower() == "true"
    },
    
    # Excel processing settings
    "excel": {
        "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "50")),
        "supported_formats": [".xlsx", ".xls"],
        "enable_formula_validation": True,
        "timeout_seconds": int(os.getenv("EXCEL_TIMEOUT_SECONDS", "300"))
    }
}


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from file or use defaults
    
    Args:
        config_path: Optional path to config file (YAML or JSON)
        
    Returns:
        Dictionary with configuration settings
    """
    config = DEFAULT_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                # Deep merge file config with defaults
                _deep_merge(config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {str(e)}. Using defaults.")
    
    return config


def _deep_merge(base_dict: Dict, update_dict: Dict):
    """
    Deep merge two dictionaries
    """
    for key, value in update_dict.items():
        if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
            _deep_merge(base_dict[key], value)
        else:
            base_dict[key] = value


# Get the actual config
CONFIG = load_config()


def main():
    """
    Main entry point for the financial knowledge graph system
    """
    print("Starting Financial Knowledge Graph System...")
    print("Enhanced with Visualization and Deep AI Analysis")
    print(f"Connecting to Neo4j at {CONFIG['database']['uri']}")
    print(f"Starting API server at {CONFIG['api']['host']}:{CONFIG['api']['port']}")
    print("Available endpoints include:")
    print("  - /api/v1/ (Standard operations)")
    print("  - /api/v1/vizai/ (Visualization and AI analysis)")
    
    uvicorn.run(
        app,
        host=CONFIG['api']['host'],
        port=CONFIG['api']['port'],
        reload=CONFIG['api']['reload']
    )


if __name__ == "__main__":
    main()