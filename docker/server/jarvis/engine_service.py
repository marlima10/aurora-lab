"""Private stateless adapter using the reviewed OpenJarvis Ollama engine."""
import json
import os
import threading
from common import Problem, authorize, config, serve

LOCK = threading.Lock()


def dispatch(method, path, headers, data):
    cfg = config()
    authorize(headers, cfg['token'])
    if method != 'POST' or path != '/generate':
        raise Problem(404, 'Operação não encontrada.')
    if not LOCK.acquire(blocking=False):
        raise Problem(429, 'A IA está respondendo outra solicitação.')
    try:
        from openjarvis.core.types import Message, Role, ToolCall
        from openjarvis.engine.ollama import OllamaEngine
        rows = data.get('messages', [])
        if not isinstance(rows, list) or not 1 <= len(rows) <= 32:
            raise Problem(400, 'Histórico inválido.')
        messages = []
        for row in rows:
            calls = [ToolCall(id=c['id'], name=c['name'], arguments=c['arguments']) for c in row.get('tool_calls', [])]
            messages.append(Message(role=Role(row['role']), content=row.get('content', ''), tool_calls=calls or None,
                                    tool_call_id=row.get('tool_call_id'), name=row.get('name')))
        engine = OllamaEngine(host='http://jarvis-ollama:11434', timeout=240)
        try:
            return engine.generate(messages, model=os.environ.get('JARVIS_MODEL', 'aurora-jarvis:1.7b'), temperature=0.2,
                                   max_tokens=256, num_ctx=8192, think=False, tools=data.get('tools', []))
        finally:
            engine._client.close()
    finally:
        LOCK.release()


if __name__ == '__main__':
    serve(dispatch)
