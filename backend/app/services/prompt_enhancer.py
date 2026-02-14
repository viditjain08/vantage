import logging
from langchain_core.messages import HumanMessage
from app.services.llm_factory import LLMFactory

logger = logging.getLogger(__name__)

ENHANCE_PROMPT = """\
You are an expert at writing system prompts for AI agents. The user has provided a rough description \
of what they want their agent to do. Your job is to rewrite it into a clear, well-structured system prompt.

The enhanced prompt MUST include the following instruction for the agent:

\"When given a task, break it down into discrete steps. For each step, decide whether you can handle it \
directly using your available tools and knowledge, or whether it requires the human to run something locally \
(e.g. a shell command, a script, a manual action). For steps that require local execution, provide the \
exact command or instructions the human should run, and ask them to paste the output back so you can continue.\"

Guidelines for enhancement:
- Keep the user's original intent and domain focus intact
- Make the prompt specific and actionable
- Add structure (role, capabilities, workflow) without being verbose
- Do NOT add tool-specific instructions (tools are configured separately)
- Return ONLY the enhanced system prompt text, nothing else

User's original prompt:
{user_prompt}
"""


class PromptEnhancer:
    @staticmethod
    async def enhance(
        user_prompt: str,
        llm_provider: str,
        llm_model: str,
        llm_provider_type: str,
        llm_api_key: str | None = None,
        llm_endpoint: str | None = None,
        llm_api_version: str | None = None,
        llm_deployment_name: str | None = None,
        llm_region: str | None = None,
    ) -> str:
        """Enhance a user-provided system prompt using the configured LLM."""
        try:
            llm = LLMFactory.create_llm(
                provider=llm_provider,
                model=llm_model,
                provider_type=llm_provider_type,
                api_key=llm_api_key,
                endpoint=llm_endpoint,
                api_version=llm_api_version,
                deployment_name=llm_deployment_name,
                region=llm_region,
            )
            message = ENHANCE_PROMPT.format(user_prompt=user_prompt)
            response = await llm.ainvoke([HumanMessage(content=message)])
            enhanced = response.content.strip()
            if enhanced:
                logger.info("System prompt enhanced successfully")
                return enhanced
        except Exception as e:
            logger.error(f"Prompt enhancement failed, using original: {e}")
        return user_prompt
