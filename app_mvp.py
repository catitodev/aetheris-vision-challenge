import os
import numpy as np
from fastrtc import Stream, ReplyOnPause, get_cloudflare_turn_credentials_async
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={"api_version": "v1alpha"}
)

# Buffer simples para a imagem (MVP)
current_image = None

def set_image(img):
    global current_image
    current_image = img
    return "Imagem atualizada. Agora fale com o Aetheris."

async def voice_handler(audio):
    global current_image
    sr, data = audio
    try:
        async with client.aio.live.connect(
            model="gemini-2.0-flash-exp",
            config={"response_modalities": ["AUDIO"]}
        ) as session:
            payload = {"audio": {"data": data.tobytes(), "mime_type": "audio/pcm;rate=16000"}}
            if current_image is not None:
                payload["image"] = current_image
            await session.send_realtime_input(**payload)
            await session.send_realtime_input(audio_stream_end=True)

            async for response in session.receive():
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if part.inline_data:
                            yield (24000, np.frombuffer(part.inline_data.data, dtype=np.int16))
    except Exception as e:
        print("Erro Gemini:", e)

stream = Stream(
    handler=ReplyOnPause(voice_handler),
    rtc_configuration=get_cloudflare_turn_credentials_async,
    modality="audio",
    mode="send-receive",
)

if __name__ == "__main__":
    # Isso abre a UI de áudio do FastRTC (com Record/VAD). Para o MVP, usaremos essa UI.
    stream.ui.launch(server_name="0.0.0.0", server_port=8080, share=True)