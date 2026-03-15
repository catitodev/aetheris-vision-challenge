import asyncio
import base64
import io
import os
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Optional, Tuple

from PIL import Image
from google import genai
from gradio_webrtc import AsyncAudioVideoStreamHandler

@dataclass
class LiveConfig:
    model: str
    enable_video: bool = True
    video_fps: float = 1.0
    ui_lang: str = "en"

class AetherisLiveHandler(AsyncAudioVideoStreamHandler):
    def __init__(self) -> None:
        super().__init__()
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Missing API key.")

        self.cfg = LiveConfig(
            model=os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash-exp"),
            enable_video=True,
            video_fps=1.0,
            ui_lang=os.getenv("AETHERIS_UI_LANG", "en"),
        )

        self.client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1alpha"},
        )

        self.session = None
        self.session_active = False
        self._last_video_ts = 0.0
        self._lock = asyncio.Lock()

    def copy(self):
        return AetherisLiveHandler()

    async def _connect(self) -> None:
        async with self._lock:
            if self.session_active:
                return
            config = {
                "response_modalities": ["AUDIO"],
                "system_instruction": "You are Aetheris. Be concise. Use the language the user speaks.",
            }
            self.session = await self.client.aio.live.connect(
                model=self.cfg.model,
                config=config,
            )
            self.session_active = True

    async def receive(self, frame: Tuple[int, bytes]) -> None:
        if not self.session_active:
            await self._connect()
        _, audio_data = frame
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")
        try:
            await self.session.send_realtime_input(
                audio={"data": audio_b64, "mime_type": "audio/pcm;rate=16000"}
            )
        except:
            self.session_active = False

    async def video_receive(self, frame: Tuple[int, bytes]) -> None:
        if not self.session_active or not self.cfg.enable_video:
            return
        now = time.time()
        if now - self._last_video_ts < (1.0 / self.cfg.video_fps):
            return
        self._last_video_ts = now
        _, image_bytes = frame
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70)
            await self.session.send_realtime_input(
                video={"data": base64.b64encode(buf.getvalue()).decode("utf-8"), "mime_type": "image/jpeg"}
            )
        except:
            pass

    async def emit(self) -> AsyncGenerator[Tuple[int, bytes], None]:
        if not self.session_active:
            return
        try:
            async for resp in self.session.receive():
                if hasattr(resp, "server_content") and resp.server_content:
                    sc = resp.server_content
                    if hasattr(sc, "model_turn") and sc.model_turn:
                        for part in sc.model_turn.parts:
                            if hasattr(part, "inline_data"):
                                yield (24000, base64.b64decode(part.inline_data.data))
        except:
            self.session_active = False

    async def video_emit(self) -> AsyncGenerator[Optional[Tuple[int, bytes]], None]:
        yield None
