# gemini_handler.py
"""
Helpers para conexão com Gemini Live.
Fornece um async-generator `stream_response` que envia áudio (+opcional imagem)
e retorna chunks de áudio (sample_rate, np.ndarray[int16]) produzidos pelo modelo.
"""

import os
import logging
from typing import Optional, AsyncGenerator

import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemini_handler")


def create_client() -> genai.Client:
    """
    Cria e retorna um cliente genai.Client a partir da variável de ambiente.
    Lança RuntimeError se a chave não estiver configurada.
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    client = genai.Client(api_key=key, http_options={"api_version": "v1alpha"})
    logger.info("Gemini client initialized")
    return client


async def stream_response(
    client: genai.Client,
    audio_bytes: bytes,
    image: Optional[np.ndarray] = None,
    model: str = "gemini-2.0-flash-exp",
) -> AsyncGenerator[tuple[int, np.ndarray], None]:
    """
    Async generator que envia áudio (bytes) e opcionalmente uma imagem (numpy array)
    para o Gemini Live e produz chunks de áudio como (sample_rate, np.ndarray).
    """
    try:
        async with client.aio.live.connect(
            model=model, config={"response_modalities": ["AUDIO"]}
        ) as session:
            payload = {
                "audio": {"data": audio_bytes, "mime_type": "audio/pcm;rate=16000"}
            }
            if image is not None:
                payload["image"] = image

            await session.send_realtime_input(**payload)
            await session.send_realtime_input(audio_stream_end=True)

            async for response in session.receive():
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if part.inline_data:
                            raw = part.inline_data.data
                            arr = np.frombuffer(raw, dtype=np.int16)
                            # yield (sample_rate, array)
                            yield (24000, arr)
    except Exception as exc:
        # Evita except "bare" e loga stacktrace para debugging
        logger.exception("Exception during stream_response: %s", exc)
        raise
