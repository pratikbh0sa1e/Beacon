"""
Centralized embedding model configuration
Change ACTIVE_MODEL to switch between embedding models
"""
from typing import Dict, Any

# ============================================
# Available Embedding Models
# ============================================

EMBEDDING_MODELS = {
    # English-only model (original)
    "bge-large-en": {
        "model_name": "BAAI/bge-large-en-v1.5",
        "dimension": 1024,
        "languages": ["English"],
        "description": "High-quality English embeddings, fastest performance",
        "use_case": "English-only documents",
        "engine": "sentence-transformers"
    },
    
    # Multilingual model (recommended for Indian govt docs)
    "bge-m3": {
        "model_name": "BAAI/bge-m3",
        "dimension": 1024,
        "languages": ["100+ languages including Hindi, Tamil, Telugu, Bengali, etc."],
        "description": "Multilingual embeddings with cross-lingual search support",
        "use_case": "Mixed language documents (English + Hindi + regional languages)",
        "engine": "sentence-transformers"
    },
    
    # Alternative multilingual option
    "multilingual-e5-large": {
        "model_name": "intfloat/multilingual-e5-large",
        "dimension": 1024,
        "languages": ["100+ languages"],
        "description": "General purpose multilingual embeddings",
        "use_case": "Broad multilingual support",
        "engine": "sentence-transformers"
    },
    
    # Smaller, faster multilingual option
    "labse": {
        "model_name": "sentence-transformers/LaBSE",
        "dimension": 768,
        "languages": ["109 languages"],
        "description": "Smaller multilingual model, faster but lower quality",
        "use_case": "Resource-constrained environments",
        "engine": "sentence-transformers"
    },
    
    # Google Gemini embeddings (cloud-based)
    "gemini-embedding": {
        "model_name": "models/embedding-001",
        "dimension": 768,
        "languages": ["100+ languages"],
        "description": "Google Gemini embeddings via API",
        "use_case": "Cloud-based embeddings, no local GPU needed",
        "engine": "gemini",
        "requires_api_key": True,
        "api_key_env": "GOOGLE_API_KEY"
    }
}

# ============================================
# ACTIVE MODEL CONFIGURATION
# ============================================
# Change this to switch embedding models
# Options: "bge-large-en", "bge-m3", "multilingual-e5-large", "labse"

ACTIVE_MODEL = "bge-m3"  # 🌍 Multilingual model (recommended)
# ACTIVE_MODEL = "bge-large-en"  # 🇬🇧 Switch back to English-only

# ============================================
# Helper Functions
# ============================================

def get_active_model_config() -> Dict[str, Any]:
    """Get configuration for the currently active model"""
    if ACTIVE_MODEL not in EMBEDDING_MODELS:
        raise ValueError(f"Invalid ACTIVE_MODEL: {ACTIVE_MODEL}. Choose from {list(EMBEDDING_MODELS.keys())}")
    
    return EMBEDDING_MODELS[ACTIVE_MODEL]


def get_model_name() -> str:
    """Get the HuggingFace model name for the active model"""
    return get_active_model_config()["model_name"]


def get_embedding_dimension() -> int:
    """Get the embedding dimension for the active model"""
    return get_active_model_config()["dimension"]


def get_active_engine_config() -> Dict[str, Any]:
    """Get full configuration for the currently active model (alias for compatibility)"""
    return get_active_model_config()


def get_model_info() -> str:
    """Get human-readable info about the active model"""
    config = get_active_model_config()
    
    info = f"""
Active Embedding Model: {ACTIVE_MODEL}
Model Name: {config['model_name']}
Dimension: {config['dimension']}
Languages: {', '.join(config['languages'])}
Description: {config['description']}
Use Case: {config['use_case']}
Engine: {config.get('engine', 'sentence-transformers')}
"""
    
    if config.get('requires_api_key'):
        info += f"Requires API Key: {config['api_key_env']}\n"
    
    return info


def list_available_models() -> None:
    """Print all available embedding models"""
    print("\n" + "="*60)
    print("Available Embedding Models")
    print("="*60)
    
    for key, config in EMBEDDING_MODELS.items():
        active_marker = "✅ ACTIVE" if key == ACTIVE_MODEL else ""
        print(f"\n{key} {active_marker}")
        print(f"  Model: {config['model_name']}")
        print(f"  Dimension: {config['dimension']}")
        print(f"  Languages: {', '.join(config['languages'])}")
        print(f"  Use Case: {config['use_case']}")
    
    print("\n" + "="*60)
    print(f"To switch models, edit ACTIVE_MODEL in embedding_config.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test the configuration
    print(get_model_info())
    list_available_models()
