"""
Shared OpenAI Service - Base service for all LLM operations
Replaces Ollama with OpenAI GPT-4 API
"""
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from config.settings import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    """Shared OpenAI service for all LLM operations"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.client = None
        self.is_initialized = False

    async def initialize(self) -> None:
        """Initialize OpenAI client"""
        if self.is_initialized:
            return

        try:
            logger.info("Initializing OpenAI service...")

            if not self.api_key:
                raise Exception("OpenAI API key not found in settings")

            # Create OpenAI async client
            self.client = AsyncOpenAI(api_key=self.api_key)

            # Test the connection
            await self._test_connection()

            self.is_initialized = True
            logger.info(f"OpenAI service ready with model: {self.model_name}")

        except Exception as e:
            logger.error(f"OpenAI service initialization failed: {str(e)}")
            self.client = None
            raise

    async def _test_connection(self):
        """Test OpenAI API connection"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            logger.info("OpenAI API connection successful")
        except Exception as e:
            raise Exception(f"Cannot connect to OpenAI API: {str(e)}")

    async def generate_response(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: Optional[float] = None,
        system_message: str = "You are a professional dental office call analyst. Provide accurate, concise analysis."
    ) -> str:
        """
        Generate LLM response using OpenAI

        Args:
            prompt: The user prompt
            max_tokens: Maximum tokens in response
            temperature: Override default temperature
            system_message: System message to set context

        Returns:
            Generated response text
        """
        try:
            if not self.is_initialized or not self.client:
                logger.warning("OpenAI service not initialized")
                return ""

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI generation error: {str(e)}")
            return ""

    async def generate_structured_response(
        self,
        prompt: str,
        response_format: Dict,
        max_tokens: int = 500,
        temperature: Optional[float] = None,
        system_message: str = "You are a professional dental office call analyst. Provide accurate analysis in JSON format."
    ) -> Dict:
        """
        Generate structured JSON response using OpenAI

        Args:
            prompt: The user prompt
            response_format: Expected JSON structure
            max_tokens: Maximum tokens in response
            temperature: Override default temperature
            system_message: System message to set context

        Returns:
            Parsed JSON response
        """
        try:
            if not self.is_initialized or not self.client:
                logger.warning("OpenAI service not initialized")
                return {}

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )

            import json
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"OpenAI structured generation error: {str(e)}")
            return {}

    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.close()
            self.client = None
        self.is_initialized = False
        logger.info("OpenAI service cleanup completed")

# Global shared instance
_openai_service = None

async def get_openai_service() -> OpenAIService:
    """Get or create shared OpenAI service instance"""
    global _openai_service

    if _openai_service is None:
        _openai_service = OpenAIService()
        await _openai_service.initialize()

    return _openai_service
