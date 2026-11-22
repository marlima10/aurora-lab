import json,html
from django.db import connection
from django.http import HttpResponse

def render_report(request):
    with connection.cursor() as c:
        c.execute("SELECT source,report FROM aurora_import_snapshot WHERE id='opengym'")
        row=c.fetchone()
    if not row:return HttpResponse('Importação ainda não concluída.',status=503)
    source,report=(json.loads(v) if isinstance(v,str) else v for v in row)
    esc=lambda v:html.escape(str(v))
    rows=''.join('<tr><td>'+esc(w.get('d',''))+'</td><td>'+esc(w.get('name',''))+'</td><td>'+esc((w.get('garminActivity') or {}).get('calories','Não informado'))+'</td></tr>' for w in source.get('workouts',[]))
    return HttpResponse('<!doctype html><html lang="pt-BR"><meta name="viewport" content="width=device-width, initial-scale=1"><title>wger · relatório da cópia</title><style>body{font:16px system-ui;max-width:1000px;margin:auto;padding:24px;background:#101820;color:#eee}a{color:#7dd3fc}td,th{padding:8px;text-align:left}table{width:100%}.scroll{overflow:auto}</style><h1>wger · ambiente de avaliação</h1><p>Cópia independente do openGym/Garmin. Alterações não voltam ao aplicativo atual.</p><p><a href="/">Abrir wger</a> · <a href="https://auroraserver.tail7d26f7.ts.net/mirror/">AuroraLAB</a></p><h2>Dados copiados</h2><pre>'+esc(json.dumps(report,indent=2))+'</pre><p>Tempo e velocidade são unidades nativas nas séries de cardio. Calorias e demais campos sem equivalente permanecem no snapshot privado. Não há sincronização contínua com o Garmin.</p><div class="scroll"><table><tr><th>Data original</th><th>Treino</th><th>Calorias Garmin</th></tr>'+rows+'</table></div></html>')
