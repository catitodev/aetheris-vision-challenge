import os
import numpy as np
import gradio as gr
from fastrtc import Stream, ReplyOnPause, WebRTC, get_cloudflare_turn_credentials_async
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={"api_version": "v1alpha"}
)

async def aetheris_chat(audio, image):
    sr, data = audio
    try:
        async with client.aio.live.connect(
            model="gemini-2.0-flash-exp", 
            config={"response_modalities": ["AUDIO"]}
        ) as session:
            # Otimização: Envia áudio e imagem
            await session.send_realtime_input(
                audio={"data": data.tobytes(), "mime_type": "audio/pcm;rate=16000"},
                image=image
            )
            await session.send_realtime_input(audio_stream_end=True)
            
            async for response in session.receive():
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if part.inline_data:
                            yield (24000, np.frombuffer(part.inline_data.data, dtype=np.int16))
    except Exception as e:
        print(f"Erro Gemini: {e}")

# Configuração do Stream
stream = Stream(
    handler=ReplyOnPause(aetheris_chat),
    rtc_configuration=get_cloudflare_turn_credentials_async,
    modality="audio-video",
    mode="send-receive",
)

# Interface Customizada com CSS para Centralização
css = """
.container { max-width: 800px; margin: auto; padding-top: 50px; }
.center-btn { display: flex; justify-content: center; padding: 20px; }
footer { visibility: hidden; } /* Esconde o rodapé padrão do Gradio */
"""

with gr.Blocks(css=css, theme=gr.themes.Soft()) as demo:
    with gr.Column(elem_classes="container"):
        gr.Markdown("# 🌌 Aetheris Live Vision")
        gr.Markdown("Aponte a câmera e fale. O Aetheris responderá após sua pausa.")
        
        # Componente WebRTC Centralizado
        rtc_component = WebRTC(
            label="Aetheris Stream",
            stream=stream,
            mode="send-receive",
            modality="audio-video"
        )
        
        with gr.Row(elem_classes="center-btn"):
            gr.Markdown("💡 **Dica:** Use o ícone de câmera no canto do vídeo para alternar para a traseira.")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8080, share=True)