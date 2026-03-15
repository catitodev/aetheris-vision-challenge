import os
import gradio as gr
from gradio_webrtc import WebRTC
from gemini_handler import AetherisLiveHandler
from dotenv import load_dotenv

load_dotenv()

handler = AetherisLiveHandler()

with gr.Blocks() as demo:
    gr.Markdown("# 🌌 Aetheris Live Audio Test")
    webrtc = WebRTC(
        label="Aetheris Voice",
        modality="audio", # Mudamos para apenas áudio para testar estabilidade
        mode="send-receive",
    )
    webrtc.stream(
        fn=handler,
        inputs=[webrtc],
        outputs=[webrtc],
        time_limit=60,
        concurrency_limit=2
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8080, share=True)