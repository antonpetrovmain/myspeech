import io
from openai import OpenAI

import config


class Transcriber:
    def __init__(self):
        self.client = OpenAI(
            api_key="local",  # Any string works for local server
            base_url=config.MLX_SERVER_URL,
        )

    def transcribe(self, audio_bytes: bytes) -> str | None:
        if not audio_bytes:
            return None

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "recording.wav"

            response = self.client.audio.transcriptions.create(
                model="mlx-community/whisper-large-v3-turbo",
                file=audio_file,
            )
            return response.text.strip() if response.text else None
        except Exception:
            return None
