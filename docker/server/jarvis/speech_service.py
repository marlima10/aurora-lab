"""Local push-to-talk transcription and speech; temporary audio is never persisted."""
import base64
import io
import os
import threading
import wave
from pathlib import Path
from common import Problem, authorize, config, serve, text

LOCK = threading.Lock()
MODEL = None


def dispatch(method, path, headers, data):
    global MODEL
    cfg = config()
    authorize(headers, cfg['token'])
    role = os.environ['SPEECH_ROLE']
    if method != 'POST' or path != '/' + role:
        raise Problem(404, 'Operação não encontrada.')
    if not LOCK.acquire(blocking=False):
        raise Problem(429, 'Serviço de voz ocupado.')
    try:
        if role == 'transcribe':
            from faster_whisper import WhisperModel
            import av
            audio = base64.b64decode(data.get('audio', ''), validate=True)
            if not audio or len(audio) > 8 * 1024 * 1024:
                raise Problem(413, 'Áudio vazio ou maior que 8 MiB.')
            # Count decoded samples before Whisper to bound compressed-audio work.
            frames = 0
            with av.open(io.BytesIO(audio)) as source:
                for frame in source.decode(audio=0):
                    frames += frame.samples / frame.sample_rate
                    if frames > 90:
                        raise Problem(413, 'Grave no máximo 90 segundos por mensagem.')
            if MODEL is None:
                MODEL = WhisperModel('/models/whisper', device='cpu', compute_type='int8', cpu_threads=2, num_workers=1, local_files_only=True)
            parts, info = MODEL.transcribe(io.BytesIO(audio), language='pt', beam_size=1, vad_filter=True)
            result = ' '.join(p.text.strip() for p in parts).strip()
            return {'text': result, 'language': info.language}
        from piper import PiperVoice
        value = text(data.get('text'), 2500)
        if MODEL is None:
            MODEL = PiperVoice.load('/models/piper/pt_BR-faber-medium.onnx')
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav:
            MODEL.synthesize_wav(value, wav)
        return {'audio': base64.b64encode(output.getvalue()).decode(), 'mime': 'audio/wav'}
    finally:
        LOCK.release()


if __name__ == '__main__':
    serve(dispatch)
