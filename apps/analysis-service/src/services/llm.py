from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from ..config import settings
from ..schemas import Segment
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        
        if not self.openai_client and not self.anthropic_client:
            logger.warning("No LLM providers configured! Analysis will run in MOCK mode.")

    async def analyze_transcript(self, transcript_text: str, provider: str = None) -> list[dict]:
        if not self.openai_client and not self.anthropic_client:
            logger.info("Running Mock Analysis")
            # Return dummy segments for testing
            return [
                {
                    "start": 10.0,
                    "end": 20.0,
                    "hook_phrase": "This is a viral hook",
                    "score": 95,
                    "hook_score": 25,
                    "emotion_score": 20,
                    "shareability_score": 25,
                    "standalone_score": 25,
                    "category": "Educational",
                    "reasoning": "Mock reasoning",
                    "caption": "Check this out #viral"
                },
                {
                    "start": 30.0,
                    "end": 45.0,
                    "hook_phrase": "Another great moment",
                    "score": 85,
                    "hook_score": 20,
                    "emotion_score": 20,
                    "shareability_score": 20,
                    "standalone_score": 25,
                    "category": "Funny",
                    "reasoning": "Mock reasoning 2",
                    "caption": "Funny clip #lol"
                }
            ]

        provider = provider or settings.DEFAULT_LLM_PROVIDER
        
        prompt = """
        You are a viral content expert. Analyze the following transcript of a video.
        Identify 3 to 10 segments that have high potential to go viral on TikTok/Shorts/Reels.
        
        For each segment, provide:
        - start: start time in seconds (approximate based on text flow, I will refine with timestamps later)
        - end: end time in seconds
        - hook_phrase: The catchy phrase that starts the clip
        - score: Total virality score (0-100)
        - hook_score: (0-25) How grabbing is the start?
        - emotion_score: (0-25) Emotional impact?
        - shareability_score: (0-25) Propensity to share?
        - standalone_score: (0-25) Does it make sense without context?
        - category: e.g., "Funny", "Educational", "Inspiring", "Controversial"
        - reasoning: Why this segment?
        - caption: A suggested caption for the post
        
        Return ONLY a valid JSON array of objects.
        
        Transcript:
        {transcript}
        """
        
        formatted_prompt = prompt.replace("{transcript}", transcript_text[:100000]) # Truncate if too long
        
        try:
            if provider == "openai" and self.openai_client:
                return await self._call_openai(formatted_prompt)
            elif provider == "anthropic" and self.anthropic_client:
                return await self._call_anthropic(formatted_prompt)
            else:
                # Fallback
                if self.openai_client:
                    return await self._call_openai(formatted_prompt)
                elif self.anthropic_client:
                    return await self._call_anthropic(formatted_prompt)
                else:
                    raise ValueError("No configured LLM provider available")
                    
        except Exception as e:
            logger.error(f"LLM analysis failed with {provider}: {e}")
            # Try fallback explicitly if first attempt failed
            if provider == "openai" and self.anthropic_client:
                logger.info("Falling back to Anthropic")
                return await self._call_anthropic(formatted_prompt)
            elif provider == "anthropic" and self.openai_client:
                logger.info("Falling back to OpenAI")
                return await self._call_openai(formatted_prompt)
            raise e

    async def _call_openai(self, prompt: str):
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a JSON-only API. Return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content).get("segments", []) if "segments" in json.loads(content) else json.loads(content)

    async def _call_anthropic(self, prompt: str):
        response = await self.anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        # Extract JSON from response text (Claude might add chatter, but prompt asks for ONLY JSON)
        # We might need to parse it out if it's not pure JSON
        content = response.content[0].text
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            return json.loads(json_str)
        return []

llm_service = LLMService()
