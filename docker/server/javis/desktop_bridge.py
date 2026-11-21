"""MCP stdio client that reconnects the fixed SSH transport for each stateless RPC."""
import json
import subprocess
import sys

def run(command, line):
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
    response = subprocess.run(command, input=line.rstrip('\r\n')+'\n', capture_output=True, text=True, encoding='utf-8', timeout=105, **options)
    if response.returncode or len(response.stdout) > 2*1024*1024:
        raise ValueError('AuroraLAB indisponível. Confira o Tailscale e tente novamente.')
    rows=[json.loads(row) for row in response.stdout.splitlines() if row.strip()]
    if len(rows)>1:
        raise ValueError('Resposta de conexão inválida.')
    return rows[0] if rows else None

if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    command=sys.argv[1:]
    if not command:raise SystemExit('Configure o transporte SSH privado.')
    for line in sys.stdin:
        request={}
        try:
            if len(line)>1024*1024:raise ValueError('Pedido acima do limite.')
            request=json.loads(line)
            result=run(command,line)
        except Exception:
            result={'jsonrpc':'2.0','id':request.get('id') if isinstance(request,dict) else None,'error':{'code':-32001,'message':'AuroraLAB indisponível. Confira o Tailscale e tente novamente.'}}
        if result is not None and isinstance(request,dict) and 'id' in request:
            print(json.dumps(result,ensure_ascii=False),flush=True)
