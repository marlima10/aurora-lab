"""Brazilian Portuguese registry and the native free Edge voice over fixed egress."""
import os
import lang_registry

def register():
    lang_registry.LANGS['pt'] = lang_registry.Lang(
        code='pt', native='Português (Brasil)', english='Portuguese (Brazil)', script='latin',
        stopwords=('de','do','da','dos','das','para','com','meu','minha','quero','você','não','uma','que','hoje','ontem','treinos'),
        request_words=('português','portugues','portuguese','português brasileiro'),
        stt='pt', tts={'edge':'pt-BR-FranciscaNeural','openai':'alloy','elevenlabs':''},
        tz_default='America/Sao_Paulo', currency='BRL', first_day=1, number_locale='pt-BR', plural=True,
        nudge='Responda em português brasileiro.',
        weekdays=('segunda-feira','terça-feira','quarta-feira','quinta-feira','sexta-feira','sábado','domingo'),
        clock_template='Agora são {hm} de {weekday}, {date}, no fuso {tz}. Considere esta data para ontem e amanhã.',
        lang_directive='Responda em português brasileiro.')

def voice_proxy():
    import edge_tts
    if getattr(edge_tts,'_aurora_proxy',False): return
    original = edge_tts.Communicate
    class ViaAurora(original):
        def __init__(self,*args,**kwargs):
            kwargs.setdefault('proxy',os.environ.get('HTTPS_PROXY'))
            super().__init__(*args,**kwargs)
    edge_tts.Communicate = ViaAurora
    original_list=edge_tts.list_voices
    async def list_voices(**kwargs):
        kwargs.setdefault('proxy',os.environ.get('HTTPS_PROXY'))
        return await original_list(**kwargs)
    edge_tts.list_voices=list_voices
    edge_tts._aurora_proxy=True
    # Upstream en=0 means Vietnamese; preserve Portuguese text and the selected Brazilian voice.
    import phien_am
    original_plan=phien_am.speech_plan
    def speech_plan(text,voice,english=None):
        if str(voice).lower().startswith('pt-br-'): return str(text or ''),voice
        return original_plan(text,voice,english)
    phien_am.speech_plan=speech_plan
