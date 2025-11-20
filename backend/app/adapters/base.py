"""
AI适配器基类
定义AI服务调用的统一接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AICheckRequest:
    """AI检查请求"""
    sql_statement: str
    explain_result: Optional[str] = None
    table_schema: Optional[str] = None


@dataclass
class AICheckResponse:
    """AI检查响应"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None


class BaseAIAdapter(ABC):
    """AI适配器抽象基类"""
    
    def __init__(self, api_key: str, api_endpoint: str, **kwargs):
        """
        初始化AI适配器
        
        Args:
            api_key: API密钥
            api_endpoint: API端点地址
            **kwargs: 其他配置参数
        """
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.config = kwargs
    
    @abstractmethod
    async def check_sql(
        self,
        request: AICheckRequest,
        system_prompt: str,
        user_prompt_template: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        **kwargs
    ) -> AICheckResponse:
        """
        检查SQL语句
        
        Args:
            request: AI检查请求
            system_prompt: 系统提示词
            user_prompt_template: 用户提示词模板
            max_tokens: 最大令牌数
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            AI检查响应
        """
        pass
    
    def build_user_prompt(self, template: str, request: AICheckRequest) -> str:
        """
        构建用户提示词
        
        Args:
            template: 提示词模板
            request: 检查请求
            
        Returns:
            构建后的提示词
        """
        user_prompt = template
        user_prompt = user_prompt.replace("{{SQL_STATEMENT}}", request.sql_statement)
        
        if request.explain_result:
            user_prompt = user_prompt.replace("{{EXPLAIN_RESULT}}", request.explain_result)
        else:
            user_prompt = user_prompt.replace("{{EXPLAIN_RESULT}}", "暂无EXPLAIN结果")
        
        if request.table_schema:
            user_prompt = user_prompt.replace("{{TABLE_SCHEMA}}", request.table_schema)
        else:
            user_prompt = user_prompt.replace("{{TABLE_SCHEMA}}", "")
        
        return user_prompt
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        pass
