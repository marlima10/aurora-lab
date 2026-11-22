"""Apply guarded language fixes to the pinned upstream dashboard, during image build."""
from pathlib import Path

def replace(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError('Upstream localization anchor mismatch: '+path.name)
    path.write_text(text.replace(old,new))

def apply(root=Path('/app/dashboard')):
    replace(root/'app.js','const voice = new JavisVoice({\n  lang: "vi-VN",','const voice = new JavisVoice({\n  lang: "pt-BR",')
    replace(root/'app.js','const liveWake = new JavisVoice({\n  lang: "vi-VN",','const liveWake = new JavisVoice({\n  lang: "pt-BR",')
    replace(root/'app.js','return (window.JavisI18n && window.JavisI18n.lang() === "en") ? "en-US" : "vi-VN";',
        'const code = window.JavisI18n && window.JavisI18n.lang(); return code === "pt" ? "pt-BR" : code === "en" ? "en-US" : "vi-VN";')
    replace(root/'voice.js','voices.find(v => v.lang === "vi-VN" && v.name.includes("Google")) ||\n        voices.find(v => v.lang === "vi-VN") ||\n        voices.find(v => v.lang.startsWith("vi")) ||',
        'voices.find(v => v.lang === this.lang && v.name.includes("Google")) ||\n        voices.find(v => v.lang === this.lang) ||\n        voices.find(v => v.lang.startsWith(this.lang.split("-")[0])) ||')
    replace(root/'voice.js','if (this.vietnameseVoice && !english) utter.voice = this.vietnameseVoice;',
        'const matching = this.synth.getVoices().find(v => v.lang === utter.lang) || this.synth.getVoices().find(v => v.lang.split("-")[0] === utter.lang.split("-")[0]); if (matching) utter.voice = matching;')
    replace(root/'index.html','<select id="voiceSel" name="voice" hidden aria-hidden="true" tabindex="-1">','<select id="voiceSel" name="voice" hidden aria-hidden="true" tabindex="-1"><option value="pt-BR-FranciscaNeural">Francisca — Português (Brasil)</option><option value="pt-BR-AntonioNeural">Antônio — Português (Brasil)</option>')
    replace(root/'index.html','<select class="js-input" id="rateSel">','<select class="js-input" id="rateSel"><option value="0.90">Calmo · 0,90×</option>')
    replace(root/'dictate.js','if (l.indexOf("en") === 0) return "en-US";', 'if (l.indexOf("pt") === 0) return "pt-BR";\n      if (l.indexOf("en") === 0) return "en-US";')
    replace(root/'voice-catalog.js','auto: "f",','"pt-br-franciscaneural": "f", "pt-br-antonioneural": "m", auto: "f",')
    replace(root/'index.html','<script src="/static/i18n/index.js', '<script src="/static/aurora-locale.js?v=38"></script><script src="/static/i18n/index.js')
    for name in ('app.js','voice.js','dictate.js','voice-catalog.js'):
        text=(root/'index.html').read_text()
        import re
        text,count=re.subn(r'(/static/'+re.escape(name)+r'\?v=)\d+',r'\g<1>aurora36',text)
        if count!=1:raise RuntimeError('Asset version anchor mismatch')
        (root/'index.html').write_text(text)

if __name__=='__main__': apply()
