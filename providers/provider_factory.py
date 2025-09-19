"""
AI提供者工厂

管理AI提供者的创建和路由。
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from providers.base_provider import AIProvider
from providers.openai_provider import OpenAIProvider
from providers.gemini_provider import GeminiProvider

# 加载环境变量
load_dotenv()


class ProviderFactory:
    """AI提供者工厂类"""

    _providers = {
        'openai': OpenAIProvider,
        'gemini': GeminiProvider,
    }

    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AIProvider:
        """创建AI提供者实例"""
        if provider_name not in cls._providers:
            raise ValueError(f"未知的提供者: {provider_name}，支持的提供者: {list(cls._providers.keys())}")

        config = config or {}
        provider_class = cls._providers[provider_name]

        # 获取配置
        if provider_name == 'openai':
            api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
            model = config.get('model') or os.getenv('OPENAI_MODEL', 'gpt-4')
            base_url = config.get('base_url') or os.getenv('OPENAI_BASE_URL')

            if not api_key:
                raise ValueError("OpenAI API密钥未配置，请设置OPENAI_API_KEY环境变量")

            kwargs = {}
            if base_url:
                kwargs['base_url'] = base_url

            return provider_class(api_key=api_key, model=model, **kwargs)

        elif provider_name == 'gemini':
            api_key = config.get('api_key') or os.getenv('GEMINI_API_KEY')
            model = config.get('model') or os.getenv('GEMINI_MODEL', 'gemini-pro')

            if not api_key:
                raise ValueError("Gemini API密钥未配置，请设置GEMINI_API_KEY环境变量")

            return provider_class(api_key=api_key, model=model)

        else:
            raise ValueError(f"未实现的提供者配置: {provider_name}")

    @classmethod
    def get_available_providers(cls) -> list:
        """获取可用的提供者列表"""
        return list(cls._providers.keys())

    @classmethod
    def register_provider(cls, name: str, provider_class):
        """注册新的提供者"""
        if not issubclass(provider_class, AIProvider):
            raise ValueError("提供者必须继承自AIProvider")

        cls._providers[name] = provider_class


class ProviderRouter:
    """AI提供者路由器"""

    def __init__(self, default_provider: str = None):
        self.providers: Dict[str, AIProvider] = {}
        self.default_provider = default_provider or os.getenv('DEFAULT_PROVIDER', 'openai')
        self.factory = ProviderFactory()

        # 初始化默认提供者
        try:
            self.providers[self.default_provider] = self.factory.create_provider(self.default_provider)
        except Exception as e:
            print(f"警告：无法初始化默认提供者 {self.default_provider}: {e}")

    def add_provider(self, name: str, config: Optional[Dict[str, Any]] = None):
        """添加AI提供者"""
        try:
            provider = self.factory.create_provider(name, config)
            self.providers[name] = provider
            return provider
        except Exception as e:
            print(f"添加提供者 {name} 失败: {e}")
            return None

    def get_provider(self, name: Optional[str] = None) -> AIProvider:
        """获取AI提供者"""
        provider_name = name or self.default_provider

        if provider_name not in self.providers:
            # 尝试创建提供者
            provider = self.add_provider(provider_name)
            if not provider:
                raise RuntimeError(f"无法获取提供者: {provider_name}")

        return self.providers[provider_name]

    async def execute_with_fallback(
        self,
        method_name: str,
        *args,
        provider_name: Optional[str] = None,
        **kwargs
    ):
        """带回退机制的执行"""
        primary_provider = provider_name or self.default_provider
        provider_names = [primary_provider]

        # 添加其他可用提供者作为回退
        for name in self.providers:
            if name != primary_provider and self.providers[name].is_healthy:
                provider_names.append(name)

        last_exception = None

        for name in provider_names:
            try:
                provider = self.get_provider(name)
                method = getattr(provider, method_name)
                result = await method(*args, **kwargs)
                return result

            except Exception as e:
                last_exception = e
                print(f"提供者 {name} 执行失败: {e}")
                continue

        # 所有提供者都失败了
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"没有可用的提供者执行方法: {method_name}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取所有提供者的统计信息"""
        stats = {}
        for name, provider in self.providers.items():
            stats[name] = provider.get_statistics()

        return {
            'providers': stats,
            'default_provider': self.default_provider,
            'total_providers': len(self.providers),
            'healthy_providers': sum(1 for p in self.providers.values() if p.is_healthy)
        }

    def reset_all_statistics(self):
        """重置所有提供者的统计信息"""
        for provider in self.providers.values():
            provider.reset_statistics()

    @property
    def available_providers(self) -> list:
        """获取当前可用的提供者列表"""
        return list(self.providers.keys())

    @property
    def healthy_providers(self) -> list:
        """获取健康的提供者列表"""
        return [name for name, provider in self.providers.items() if provider.is_healthy]

    def switch_default_provider(self, provider_name: str):
        """切换默认提供者"""
        if provider_name not in self.providers:
            raise ValueError(f"提供者 {provider_name} 不存在")

        self.default_provider = provider_name