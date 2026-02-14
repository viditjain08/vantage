from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from app.core.config import settings


class LLMFactory:
    """Factory for creating LLM instances based on provider and credential type."""
    
    @staticmethod
    def create_llm(
        provider: str,
        model: str,
        provider_type: str,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        deployment_name: Optional[str] = None,
        region: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> BaseChatModel:
        """
        Create an LLM instance based on the provider and credential configuration.
        
        Args:
            provider: 'openai' or 'claude'
            model: Model name (e.g., 'gpt-4', 'claude-3-opus-20240229')
            provider_type: 'direct', 'aws', or 'azure'
            api_key: API key for authentication
            endpoint: Endpoint URL (for Azure)
            api_version: API version (for Azure)
            deployment_name: Deployment name (for Azure)
            region: AWS region (for AWS Bedrock)
            temperature: Temperature for the model
            
        Returns:
            BaseChatModel instance
        """
        provider = provider.lower()
        provider_type = provider_type.lower()
        
        if provider == "openai":
            return LLMFactory._create_openai_llm(
                model=model,
                provider_type=provider_type,
                api_key=api_key,
                endpoint=endpoint,
                api_version=api_version,
                deployment_name=deployment_name,
                region=region,
                temperature=temperature,
            )
        elif provider == "claude":
            return LLMFactory._create_claude_llm(
                model=model,
                provider_type=provider_type,
                api_key=api_key,
                endpoint=endpoint,
                api_version=api_version,
                deployment_name=deployment_name,
                region=region,
                temperature=temperature,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @staticmethod
    def _create_openai_llm(
        model: str,
        provider_type: str,
        api_key: Optional[str],
        endpoint: Optional[str],
        api_version: Optional[str],
        deployment_name: Optional[str],
        region: Optional[str],
        temperature: Optional[float],
    ) -> BaseChatModel:
        """Create OpenAI LLM instance."""
        
        if provider_type == "direct":
            # Direct OpenAI API
            kwargs = dict(
                model=model,
                api_key=api_key or settings.OPENAI_API_KEY,
            )
            if temperature is not None:
                kwargs["temperature"] = temperature
            return ChatOpenAI(**kwargs)

        elif provider_type == "azure":
            # Azure OpenAI
            kwargs = dict(
                azure_endpoint=endpoint or settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=deployment_name or settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                openai_api_version=api_version or settings.AZURE_OPENAI_API_VERSION,
                api_key=api_key or settings.AZURE_OPENAI_API_KEY,
            )
            if temperature is not None:
                kwargs["temperature"] = temperature
            return AzureChatOpenAI(**kwargs)

        elif provider_type == "aws":
            # AWS Bedrock OpenAI (if available)
            # Note: This requires langchain-aws package
            try:
                from langchain_aws import ChatBedrockConverse
                kwargs = dict(
                    model=model,
                    region_name=region or settings.AWS_OPENAI_REGION,
                )
                if temperature is not None:
                    kwargs["temperature"] = temperature
                return ChatBedrockConverse(**kwargs)
            except ImportError:
                raise ImportError(
                    "AWS Bedrock support requires 'langchain-aws' package. "
                    "Install it with: pip install langchain-aws"
                )
        
        else:
            raise ValueError(f"Unsupported provider_type for OpenAI: {provider_type}")
    
    @staticmethod
    def _create_claude_llm(
        model: str,
        provider_type: str,
        api_key: Optional[str],
        endpoint: Optional[str],
        api_version: Optional[str],
        deployment_name: Optional[str],
        region: Optional[str],
        temperature: Optional[float],
    ) -> BaseChatModel:
        """Create Claude LLM instance."""

        if provider_type == "direct":
            # Direct Anthropic API
            kwargs = dict(
                model=model,
                api_key=api_key or settings.ANTHROPIC_API_KEY,
            )
            if temperature is not None:
                kwargs["temperature"] = temperature
            return ChatAnthropic(**kwargs)

        elif provider_type == "azure":
            # Azure Claude (using Azure OpenAI-compatible endpoint)
            # Note: This might require custom implementation depending on Azure's Claude offering
            kwargs = dict(
                azure_endpoint=endpoint or settings.AZURE_CLAUDE_ENDPOINT,
                azure_deployment=deployment_name or settings.AZURE_CLAUDE_DEPLOYMENT_NAME,
                openai_api_version=api_version or settings.AZURE_CLAUDE_API_VERSION,
                api_key=api_key or settings.AZURE_CLAUDE_API_KEY,
            )
            if temperature is not None:
                kwargs["temperature"] = temperature
            return AzureChatOpenAI(**kwargs)

        elif provider_type == "aws":
            # AWS Bedrock Claude
            try:
                from langchain_aws import ChatBedrockConverse
                kwargs = dict(
                    model=model,
                    region_name=region or settings.AWS_CLAUDE_REGION,
                )
                if temperature is not None:
                    kwargs["temperature"] = temperature
                return ChatBedrockConverse(**kwargs)
            except ImportError:
                raise ImportError(
                    "AWS Bedrock support requires 'langchain-aws' package. "
                    "Install it with: pip install langchain-aws"
                )
        
        else:
            raise ValueError(f"Unsupported provider_type for Claude: {provider_type}")

