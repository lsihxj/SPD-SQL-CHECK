"""
通用HTTP适配器
用于支持国内大模型（通义千问、文心一言等）
"""
import httpx
from typing import Optional, Dict, Any
from .base import BaseAIAdapter, AICheckRequest, AICheckResponse


class GenericHTTPAdapter(BaseAIAdapter):
    """通用HTTP API适配器"""
    
    def __init__(self, api_key: str, api_endpoint: str, **kwargs):
        """
        初始化通用适配器
        
        Args:
            api_key: API密钥
            api_endpoint: API端点
            **kwargs: 其他配置
        """
        super().__init__(api_key, api_endpoint, **kwargs)
        self.timeout = kwargs.get('timeout', 60.0)
    
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
        使用通用HTTP API检查SQL
        
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
            
            # 构建请求体（通用格式）
            model_name = kwargs.get('model_name', 'default-model')
            
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # 添加自定义请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 发送HTTP请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_endpoint,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                # 解析响应（假设返回格式类似OpenAI）
                response_data = response.json()
                
                # 尝试从多种可能的响应格式中提取结果
                result_content = None
                if "choices" in response_data:
                    result_content = response_data["choices"][0]["message"]["content"]
                elif "output" in response_data:
                    result_content = response_data["output"].get("text", "")
                elif "result" in response_data:
                    result_content = response_data["result"]
                else:
                    result_content = str(response_data)
                
                return AICheckResponse(
                    success=True,
                    result=result_content,
                    raw_response=str(response_data)
                )
                
        except Exception as e:
            return AICheckResponse(
                success=False,
                error=str(e)
            )
    
    async def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.api_endpoint.replace("/chat/completions", "/models"),
                    headers=headers
                )
                return response.status_code == 200
        except Exception:
            return False
