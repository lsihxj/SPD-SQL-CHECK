"""
OpenAI适配器
"""
import openai
from typing import Optional
from .base import BaseAIAdapter, AICheckRequest, AICheckResponse


class OpenAIAdapter(BaseAIAdapter):
    """OpenAI API适配器"""
    
    def __init__(self, api_key: str, api_endpoint: str = "https://api.openai.com/v1", **kwargs):
        """
        初始化OpenAI适配器
        
        Args:
            api_key: OpenAI API密钥
            api_endpoint: API端点
            **kwargs: 其他配置
        """
        super().__init__(api_key, api_endpoint, **kwargs)
        self.client = openai.AsyncOpenAI(
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
        使用OpenAI检查SQL
        
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
            model_name = kwargs.get('model_name', 'gpt-4')
            
            # 调用OpenAI API（非流式）
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False  # 此方法不使用流式
            )
            
            # 提取结果
            result_content = response.choices[0].message.content
            
            return AICheckResponse(
                success=True,
                result=result_content,
                raw_response=result_content
            )
            
        except openai.NotFoundError as e:
            # 404 错误 - 模型不存在或端点错误
            model_name = kwargs.get('model_name', 'unknown')
            return AICheckResponse(
                success=False,
                error=f"API调用404错误：\n"
                      f"1. 模型 '{model_name}' 不存在或不可用\n"
                      f"2. API端点不正确: {self.api_endpoint}\n"
                      f"3. 请检查：\n"
                      f"   - DeepSeek的端点应为: https://api.deepseek.com\n"
                      f"   - 模型名称应为: deepseek-chat 或 deepseek-coder\n"
                      f"\n原始错误: {str(e)}"
            )
        except openai.AuthenticationError as e:
            # 401 错误 - 认证失败
            return AICheckResponse(
                success=False,
                error=f"API密钥认证失败：{str(e)}\n请检查API密钥是否正确。"
            )
        except openai.RateLimitError as e:
            # 429 错误 - 请求频率限制
            return AICheckResponse(
                success=False,
                error=f"请求频率超限：{str(e)}\n请稍后再试或检查账户额度。"
            )
        except openai.APIConnectionError as e:
            # 网络连接错误
            return AICheckResponse(
                success=False,
                error=f"网络连接失败：{str(e)}\n请检查网络连接和代理设置。"
            )
        except Exception as e:
            # 其他错误
            error_type = type(e).__name__
            return AICheckResponse(
                success=False,
                error=f"[{error_type}] {str(e)}"
            )
    
    async def check_sql_stream(self, request: AICheckRequest, system_prompt: str, user_prompt_template: str, max_tokens: int = 4000, temperature: float = 0.7, **kwargs):
        """
        使用OpenAI检查SQL（流式输出）
        
        Args:
            request: AI检查请求
            system_prompt: 系统提示词
            user_prompt_template: 用户提示词模板
            max_tokens: 最大令牌数
            temperature: 温度参数
            **kwargs: 其他参数
            
        Yields:
            流式响应块
        """
        try:
            # 构建用户提示词
            user_prompt = self.build_user_prompt(user_prompt_template, request)
            
            # 获取模型名称
            model_name = kwargs.get('model_name', 'gpt-4')
            
            # 调用OpenAI API（流式）
            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            # 返回流式数据
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                        
        except Exception as e:
            error_type = type(e).__name__
            yield f"\n\n[错误: {error_type}] {str(e)}"
    
    async def test_connection(self) -> bool:
        """
        测试OpenAI API连接
        
        Returns:
            连接是否成功
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False
