"""
AI适配器模块
"""
from .base import BaseAIAdapter, AICheckRequest, AICheckResponse
from .openai_adapter import OpenAIAdapter
from .claude_adapter import ClaudeAdapter
from .generic_adapter import GenericHTTPAdapter
from .factory import AIAdapterFactory

__all__ = [
    'BaseAIAdapter',
    'AICheckRequest',
    'AICheckResponse',
    'OpenAIAdapter',
    'ClaudeAdapter',
    'GenericHTTPAdapter',
    'AIAdapterFactory'
]
