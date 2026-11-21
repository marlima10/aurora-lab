"""Explicit voice-model download job; never runs inside the audio request handler."""
import json
import os
import urllib.request
from pathlib import Path
from huggingface_hub import snapshot_download

root = Path('/models')
root.mkdir(exist_ok=True)
snapshot_download('Systran/faster-whisper-base', revision='ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66', local_dir=str(root/'whisper'))
dest = root/'piper'
dest.mkdir(exist_ok=True)
base = 'https://huggingface.co/rhasspy/piper-voices/resolve/e9c8a39444359388adaa94255becb37a5a2b8e51/pt/pt_BR/faber/medium/'
for name in ('pt_BR-faber-medium.onnx', 'pt_BR-faber-medium.onnx.json', 'MODEL_CARD'):
    target = dest/name
    if not target.exists():
        with urllib.request.urlopen(base+name, timeout=120) as response, target.with_suffix(target.suffix+'.part').open('wb') as out:
            while chunk := response.read(1024*1024):
                out.write(chunk)
        target.with_suffix(target.suffix+'.part').replace(target)
print(json.dumps({'voiceModelsReady': True}))
