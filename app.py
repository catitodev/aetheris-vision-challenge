import os
import logging
import numpy as np
import gradio as gr
from dotenv import load_dotenv
from fastrtc import Stream, ReplyOnPause, get_cloudflare_turn_credentials_async
from gemini_handler import create_client, stream_response

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID", "aetheris-vision-challenge")
if not GEMINI_API_KEY or not HUGGINGFACE_API_KEY:
    raise SystemExit("ENV VARS MISSING")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aetheris_app")

try:
    client = create_client()
except RuntimeError as exc:
    logger.error("Gemini client init failed: %s", exc)
    raise

current_context_image: None | np.ndarray = None

def set_context_image(img: np.ndarray) -> str:
    global current_context_image
    current_context_image = img
    return "Imagem carregada — pronto para análise por voz."

async def aetheris_voice_with_image(audio, image=None):
    global current_context_image
    try:
        if audio is None:
            logger.warning("Handler chamado sem áudio.")
            return
        sr, data = audio
        audio_bytes = data.tobytes()
        if image is not None:
            current_context_image = image
        async for sample_rate, arr in stream_response(
            client, audio_bytes, image=current_context_image
        ):
            yield (sample_rate, arr)
    except Exception as exc:
        logger.exception("Erro no handler aetheris_voice_with_image: %s", exc)

img_component = gr.Image(label="Snapshot / Print (photo or upload)", type="numpy")

stream = Stream(
    handler=ReplyOnPause(aetheris_voice_with_image),
    rtc_configuration=get_cloudflare_turn_credentials_async,
    modality="audio",
    mode="send-receive",
    additional_inputs=[img_component],
)

if __name__ == "__main__":
    stream.ui.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 8080)), share=True)