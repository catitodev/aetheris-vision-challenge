# app.py - Aetheris consolidado (Snapshot-to-Voice MVP)
"""
Entrada principal para o MVP. Usa FastRTC Stream com ReplyOnPause para enviar
áudio ao Gemini e aceita um input de imagem (snapshot) como contexto.
"""

import os
import logging
import traceback

import numpy as np
import gradio as gr
from dotenv import load_dotenv
from fastrtc import Stream, ReplyOnPause, get_cloudflare_turn_credentials_async

from gemini_handler import create_client, stream_response

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aetheris_app")

# Inicializa o cliente Gemini
try:
    client = create_client()
except RuntimeError as exc:
    logger.error("Gemini client init failed: %s", exc)
    raise

# Estado do contexto visual (neste MVP, mantemos apenas a última imagem)
current_context_image: None | np.ndarray = None


def set_context_image(img: np.ndarray) -> str:
    """
    Atualiza a imagem de contexto. Chamado pelo componente de upload.
    """
    global current_context_image
    current_context_image = img
    return "Imagem carregada — pronto para análise por voz."


async def aetheris_voice_with_image(audio, image=None):
    """
    Handler passado ao Stream. Recebe audio como (sample_rate, numpy_array).
    Caso a imagem seja passada ao handler, atualiza o contexto.
    Produz via yield os chunks de áudio retornados pelo Gemini.
    """
    global current_context_image
    try:
        if audio is None:
            logger.warning("Handler chamado sem áudio.")
            return

        sr, data = audio
        audio_bytes = data.tobytes()

        # Se a imagem foi passada diretamente ao handler, sobrescreve o contexto
        if image is not None:
            current_context_image = image

        # Usa o helper de gemini_handler para ler o generator de resposta
        async for sample_rate, arr in stream_response(
            client, audio_bytes, image=current_context_image
        ):
            yield (sample_rate, arr)
    except Exception as exc:
        logger.exception("Erro no handler aetheris_voice_with_image: %s", exc)
        # não re-raise; Stream deve lidar com a desconexão


# Componente de imagem para a UI do Stream
img_component = gr.Image(label="Snapshot / Print (photo or upload)", type="numpy")

# Configura o Stream do FastRTC
stream = Stream(
    handler=ReplyOnPause(aetheris_voice_with_image),
    rtc_configuration=get_cloudflare_turn_credentials_async,
    modality="audio",
    mode="send-receive",
    additional_inputs=[img_component],
)

if __name__ == "__main__":
    # Para testes locais e mobile: share=True cria link gradio.live temporário
    stream.ui.launch(server_name="0.0.0.0", server_port=8080, share=True)
