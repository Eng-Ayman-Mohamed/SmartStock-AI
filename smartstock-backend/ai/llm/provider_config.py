"""
provider_config.py — Multi-provider LLM configuration.

Supports OpenAI, Groq, and Google Gemini as LLM/embedding providers.
Controlled by LLM_PROVIDER env var (default: openai).

Groq uses OpenAI-compatible API, so ChatOpenAI works with a base_url override.
Gemini uses langchain-google-genai for embeddings.
"""

import logging
import os

from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

PROVIDER = os.getenv('LLM_PROVIDER', 'openai').lower()
WHISPER_PROVIDER = os.getenv('LLM_WHISPER_PROVIDER', PROVIDER).lower()

# Provider-specific configuration
_PROVIDERS = {
    'openai': {
        'chat_model': 'gpt-4o',
        'chat_model_mini': 'gpt-4o-mini',
        'embedding_model': 'text-embedding-3-small',
        'embedding_dimensions': 1536,
        'whisper_model': 'whisper-1',
        'vision_model': 'gpt-4o',
        'supports_vision': True,
        'base_url': None,
        'api_key_env': 'OPENAI_API_KEY',
    },
    'groq': {
        'chat_model': 'llama-3.3-70b-versatile',
        'chat_model_mini': 'llama-3.1-8b-instant',
        'embedding_model': None,  # Groq has no embedding API
        'embedding_dimensions': None,
        'whisper_model': 'whisper-large-v3',
        'vision_model': 'meta-llama/llama-4-scout-17b-16e-instruct',
        'supports_vision': True,
        'base_url': 'https://api.groq.com/openai/v1',
        'api_key_env': 'GROQ_API_KEY',
    },
    'gemini': {
        'chat_model': 'gemini-2.0-flash',
        'chat_model_mini': 'gemini-2.0-flash',
        'embedding_model': 'gemini-embedding-001',
        'embedding_dimensions': 768,
        'whisper_model': None,  # Gemini has no Whisper equivalent
        'vision_model': 'gemini-2.0-flash',
        'supports_vision': True,
        'base_url': None,
        'api_key_env': 'GOOGLE_API_KEY',
    },
}


def get_provider_config():
    """Return the config dict for the active provider."""
    return _PROVIDERS[PROVIDER]


def get_api_key():
    """Get the API key for the active provider."""
    return get_api_key_for_provider(PROVIDER)


def get_api_key_for_provider(provider_name: str) -> str:
    """Get the API key for a specific provider."""
    config = _PROVIDERS[provider_name]
    key = os.getenv(config['api_key_env'], '')
    if not key:
        raise ValueError(
            f'{config["api_key_env"]} is required for {provider_name} provider. '
            f'Set LLM_PROVIDER to "openai" or provide the key.'
        )
    return key


def get_chat_llm(temperature=0, model_override=None):
    """Get a chat LLM instance for the active provider."""
    config = get_provider_config()
    model = model_override or config['chat_model']
    api_key = get_api_key()

    if PROVIDER == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
        )

    from langchain_openai import ChatOpenAI

    kwargs = {
        'model': model,
        'temperature': temperature,
        'api_key': api_key,
        'request_timeout': 8,
        'max_retries': 2,
    }
    if config['base_url']:
        kwargs['base_url'] = config['base_url']

    return ChatOpenAI(**kwargs)


def get_chat_llm_mini(temperature=0):
    """Get a smaller/cheaper chat model for classification tasks."""
    config = get_provider_config()
    return get_chat_llm(temperature=temperature, model_override=config['chat_model_mini'])


def get_embeddings():
    """Get an embeddings model instance for the active provider.

    Falls back to Gemini if the active provider has no embedding API (e.g. Groq).
    """
    config = get_provider_config()

    # If the active provider supports embeddings, use it
    if config['embedding_model']:
        if PROVIDER == 'gemini':
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            return GoogleGenerativeAIEmbeddings(
                model=config['embedding_model'],
                google_api_key=get_api_key(),
            )

        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=config['embedding_model'],
            api_key=get_api_key(),
            **({'base_url': config['base_url']} if config['base_url'] else {}),
        )

    # Fallback: use Gemini for embeddings if provider doesn't support them
    gemini_key = os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        logger.info('Provider %s has no embeddings — falling back to Gemini', PROVIDER)
        return GoogleGenerativeAIEmbeddings(
            model='gemini-embedding-001',
            google_api_key=gemini_key,
        )

    raise ImproperlyConfigured(
        f'Provider {PROVIDER} has no embedding API and GOOGLE_API_KEY is not set. '
        'Set GOOGLE_API_KEY or switch to OpenAI/Gemini for embeddings.'
    )


def get_whisper_config():
    """Get the whisper config for the whisper provider."""
    return _PROVIDERS[WHISPER_PROVIDER]


def get_whisper_client():
    """Get a client for speech-to-text transcription.

    Uses LLM_WHISPER_PROVIDER if set, otherwise falls back to the main provider.
    """
    if WHISPER_PROVIDER == 'groq':
        from groq import Groq

        return Groq(api_key=get_api_key_for_provider('groq'))

    # OpenAI
    from openai import OpenAI

    return OpenAI(api_key=get_api_key_for_provider('openai'))


def get_vision_client():
    """Get a client for vision/image analysis."""
    if PROVIDER == 'groq':
        from openai import OpenAI

        return OpenAI(
            api_key=get_api_key(),
            base_url='https://api.groq.com/openai/v1',
        )

    # OpenAI
    from openai import OpenAI

    return OpenAI(api_key=get_api_key())
