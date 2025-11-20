"""
AI适配器工厂
"""
from typing import Dict, Type
from .base import BaseAIAdapter
from .openai_adapter import OpenAIAdapter
from .claude_adapter import ClaudeAdapter
from .generic_adapter import GenericHTTPAdapter


class AIAdapterFactory:
    """AI适配器工厂"""
    
    # 适配器注册表
    _adapters: Dict[str, Type[BaseAIAdapter]] = {
        'openai': OpenAIAdapter,
        'claude': ClaudeAdapter,
        'deepseek': OpenAIAdapter,  # DeepSeek (兼容OpenAI格式)
        'qwen': GenericHTTPAdapter,  # 通义千问
        'wenxin': GenericHTTPAdapter,  # 文心一言
        'generic': GenericHTTPAdapter  # 通用适配器
    }
    
    @classmethod
    def create_adapter(
        cls,
        provider_name: str,
        api_key: str,
        api_endpoint: str,
        **kwargs
    ) -> BaseAIAdapter:
        """
        创建AI适配器实例
        
        Args:
            provider_name: 厂家名称
            api_key: API密钥
            api_endpoint: API端点
            **kwargs: 其他配置
            
        Returns:
            BaseAIAdapter实例
            
        Raises:
            ValueError: 不支持的厂家名称
        """
        adapter_class = cls._adapters.get(provider_name.lower())
        
        if adapter_class is None:
            supported = ', '.join(cls.get_supported_providers())
            raise ValueError(
                f"不支持的AI发布商: '{provider_name}'\n"
                f"当前支持的发布商: {supported}\n"
                f"请检查AI厂家配置中的'厂家标识'字段是否正确。"
            )
        
        return adapter_class(api_key, api_endpoint, **kwargs)
    
    @classmethod
    def register_adapter(cls, provider_name: str, adapter_class: Type[BaseAIAdapter]):
        """
        注册新的适配器
        
        Args:
            provider_name: 厂家名称
            adapter_class: 适配器类
        """
        cls._adapters[provider_name.lower()] = adapter_class
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """
        获取支持的厂家列表
        
        Returns:
            厂家名称列表
        """
        return list(cls._adapters.keys())
