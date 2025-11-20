"""
Claude (Anthropic) 适配器
"""
import anthropic
from typing import Optional
from .base import BaseAIAdapter, AICheckRequest, AICheckResponse


class ClaudeAdapter(BaseAIAdapter):
    """Claude API适配器"""
    
    def __init__(self, api_key: str, api_endpoint: str = "https://api.anthropic.com", **kwargs):
        """
        初始化Claude适配器
        
        Args:
            api_key: Anthropic API密钥
            api_endpoint: API端点
            **kwargs: 其他配置
        """
        super().__init__(api_key, api_endpoint, **kwargs)
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            base_url=api_endpoint
        )
    
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
        使用Claude检查SQL
        
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
        try:
            # 构建用户提示词
            user_prompt = self.build_user_prompt(user_prompt_template, request)
            
            # 获取模型名称
            model_name = kwargs.get('model_name', 'claude-3-sonnet-20240229')
            
            # 调用Claude API
            response = await self.client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # 提取结果
            result_content = response.content[0].text
            
            return AICheckResponse(
                success=True,
                result=result_content,
                raw_response=result_content
            )
            
        except Exception as e:
            return AICheckResponse(
                success=False,
                error=str(e)
            )
    
    async def test_connection(self) -> bool:
        """
        测试Claude API连接
        
        Returns:
            连接是否成功
        """
        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False
