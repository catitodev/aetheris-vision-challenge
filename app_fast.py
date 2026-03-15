import os
import asyncio
import numpy as np
from fastrtc import Stream, ReplyOnPause
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={"api_version": "v1alpha"}
)

async def gemini_voice_chat(audio):
    # O FastRTC entrega (sample_rate, numpy_array)
    sr, data = audio
    # Converte para bytes PCM 16-bit
    audio_bytes = data.tobytes()
    
    # Conexão direta com o Gemini Live
    async with client.aio.live.connect(
        model="gemini-2.0-flash-exp", 
        config={"response_modalities": ["AUDIO"]}
    ) as session:
        # Envia o áudio capturado após a pausa
        await session.send_realtime_input(
            audio={"data": audio_bytes, "mime_type": "audio/pcm;rate=16000"}
        )
        # Avisa que o turno do usuário acabou
        await session.send_realtime_input(audio_stream_end=True)
        
        # Recebe a resposta e faz o yield imediato para o WebRTC
        async for response in session.receive():
            if response.server_content and response.server_content.model_turn:
                for part in response.server_content.model_turn.parts:
                    if part.inline_data:
                        # Gemini retorna 24kHz, FastRTC aceita e converte se necessário
                        yield (24000, np.frombuffer(part.inline_data.data, dtype=np.int16))

# Configuração do Stream com detecção de pausa automática (VAD)
stream = Stream(
    handler=ReplyOnPause(gemini_voice_chat),
    modality="audio",
    mode="send-receive",
)

if __name__ == "__main__":
    # O FastRTC usa o .ui.launch() para criar a interface Gradio automaticamente
    stream.ui.launch(server_name="0.0.0.0", server_port=8080, share=True)