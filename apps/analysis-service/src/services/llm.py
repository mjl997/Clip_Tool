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

    async def analyze_transcript(self, transcript_text: str, audio_context: str = "", provider: str = None) -> list[dict]:
        if not self.openai_client and not self.anthropic_client:
            logger.info("Running Mock Analysis")
            # Return dummy segments for testing
            return [
                {
                    "start": 10.0,
                    "end": 20.0,
                    "hook_phrase": "This is a viral hook",
                    "score": 95,
                    "score_breakdown": {
                        "hook_score": 25,
                        "emotion_score": 20,
                        "shareability_score": 25,
                        "standalone_score": 25
                    },
                    "category": "Educational",
                    "reasoning": "Mock reasoning",
                    "caption": "Check this out #viral"
                },
                {
                    "start": 30.0,
                    "end": 45.0,
                    "hook_phrase": "Another great moment",
                    "score": 85,
                    "score_breakdown": {
                        "hook_score": 20,
                        "emotion_score": 20,
                        "shareability_score": 20,
                        "standalone_score": 25
                    },
                    "category": "Funny",
                    "reasoning": "Mock reasoning 2",
                    "caption": "Funny clip #lol"
                }
            ]

        provider = provider or settings.DEFAULT_LLM_PROVIDER
        
        prompt = """
        Eres un editor de video experto especializado en contenido viral para TikTok, Instagram Reels y YouTube Shorts. Tu trabajo es identificar los segmentos de un video largo que tienen mayor probabilidad de volverse virales como clips independientes.

        TRANSCRIPCIÓN CON TIMESTAMPS:
        {transcript}

        {audio_context}

        INSTRUCCIONES:
        Analiza la transcripción completa e identifica entre 3 y 8 segmentos con potencial viral. Cada segmento debe durar entre 15 y 60 segundos.

        CRITERIOS DE SCORING (cada uno vale 0-25 puntos, total máximo 100):

        1. HOOK STRENGTH (0-25): ¿Los primeros 3 segundos del segmento generan curiosidad inmediata? Busca: preguntas retóricas, declaraciones controversiales, datos sorprendentes, "la gente no sabe que...", promesas de revelación, contradicciones. Un hook de score 20+ debe hacer que alguien deje de scrollear.

        2. EMOTIONAL ARC (0-25): ¿El segmento tiene un arco emocional completo dentro de su duración? Busca: setup → tensión → resolución, humor con punchline, momento de revelación/plot twist, vulnerabilidad auténtica, indignación justificada. NO selecciones fragmentos que empiecen o terminen a mitad de una idea.

        3. SHAREABILITY (0-25): ¿Alguien enviaría este clip a un amigo o lo compartiría en su historia? Busca: "esto le pasa a todo el mundo", opiniones polarizantes, consejos ultra-prácticos en <30 segundos, momentos de "no puedo creer que dijo eso", validación emocional ("por fin alguien lo dice").

        4. STANDALONE CLARITY (0-25): ¿Se entiende el segmento SIN haber visto el resto del video? Si requiere contexto previo para tener sentido, el score debe ser bajo. El clip ideal funciona como pieza independiente.

        REGLAS ESTRICTAS:
        - Mínimo 3 segmentos, máximo 8
        - Duración de cada segmento: 15-60 segundos
        - No puede haber overlap entre segmentos
        - El start_time debe coincidir con el inicio de una oración (no cortar a mitad de palabra)
        - El end_time debe coincidir con el final natural de una idea (pausa, cambio de tema, punchline)
        - Ordena los segmentos de mayor a menor viral_score
        - Solo incluye segmentos con score >= 50. Si no hay ninguno >= 50, retorna los 3 mejores sin importar el score
        - NO inventes timestamps que no existan en la transcripción

        FORMATO DE RESPUESTA (JSON estricto, sin markdown, sin texto adicional):
        {
          "segments": [
            {
              "start": 124.5,
              "end": 158.2,
              "score": 82,
              "score_breakdown": {
                "hook_score": 22,
                "emotion_score": 20,
                "shareability_score": 23,
                "standalone_score": 17
              },
              "hook_phrase": "La frase exacta que abre el clip",
              "category": "insight",
              "reasoning": "Una oración explicando por qué este segmento es viral",
              "caption": "Texto corto para el post en redes",
              "suggested_hashtags": ["#tag1", "#tag2", "#tag3"]
            }
          ],
          "video_summary": "Resumen de 1 oración del tema principal del video",
          "total_segments_found": 5
        }

        Las categorías válidas son: humor | insight | controversial | emotional | educational | shocking | motivational | storytelling

        Analiza la transcripción completa antes de seleccionar. No te quedes solo con los primeros minutos.
        """
        
        formatted_prompt = prompt.replace("{transcript}", transcript_text[:100000]).replace("{audio_context}", audio_context) # Truncate if too long
        
        # Log prompt for debugging
        logger.debug(f"LLM Prompt: {formatted_prompt[:500]}...")
        
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
            
            # Check for 503, 429, or capacity/limit errors
            error_str = str(e).lower()
            is_overload = "503" in error_str or "capacity" in error_str or "429" in error_str or "rate limit" in error_str
            
            # Try fallback explicitly if first attempt failed
            if provider == "openai" and self.anthropic_client:
                logger.info("Falling back to Anthropic")
                return await self._call_anthropic(formatted_prompt)
            elif provider == "anthropic" and self.openai_client:
                logger.info("Falling back to OpenAI")
                return await self._call_openai(formatted_prompt)
            
            # If no fallback available and it's an overload/rate limit error, wait and retry once
            if is_overload:
                wait_time = 20 # Wait longer for rate limits (16.5s in error message)
                logger.info(f"Service overloaded/rate limited. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                
                # Try with a cheaper/faster model for retry if possible
                if provider == "openai":
                    # Fallback to gpt-3.5-turbo if gpt-4 is limited? 
                    # Or just retry same model. Let's try same model for now but maybe we should use gpt-3.5-turbo-0125
                    return await self._call_openai(formatted_prompt, model="gpt-3.5-turbo-0125")
                elif provider == "anthropic":
                    return await self._call_anthropic(formatted_prompt, model="claude-3-haiku-20240307")
                    
            raise e

    async def _call_openai(self, prompt: str, model: str = "gpt-4-turbo-preview"):
        logger.info(f"Calling OpenAI with model: {model}")
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a JSON-only API. Return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        logger.debug(f"LLM Response: {content[:500]}...")
        
        try:
            parsed = json.loads(content)
            return parsed.get("segments", [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON: {e}")
            return []

    async def _call_anthropic(self, prompt: str, model: str = "claude-3-opus-20240229"):
        logger.info(f"Calling Anthropic with model: {model}")
        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        # Extract JSON from response text (Claude might add chatter, but prompt asks for ONLY JSON)
        # We might need to parse it out if it's not pure JSON
        content = response.content[0].text
        logger.debug(f"LLM Response: {content[:500]}...")
        
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            try:
                parsed = json.loads(json_str)
                return parsed.get("segments", [])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Anthropic JSON: {e}")
                return []
        return []

llm_service = LLMService()
