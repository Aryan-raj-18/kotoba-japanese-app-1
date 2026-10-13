"""Build the self-contained opening animation available before Python starts."""
from pathlib import Path
import base64,re
ROOT=Path(__file__).parent

def write_opening_asset(destination):
 template=(ROOT/'templates/base.html').read_text()
 start=template.index('<div class="kotoba-intro"');end=template.index('\n{% endif %}',start)
 markup=template[start:end]
 icon=base64.b64encode((ROOT/'static/icons/icon-192.png').read_bytes()).decode()
 markup=re.sub(r'\{\{ url_for\(\x27static\x27, filename=\x27icons/icon-192.png\x27\) \}\}', 'data:image/png;base64,'+icon,markup)
 assert '{{' not in markup and '{%' not in markup
 font=base64.b64encode((ROOT/'static/fonts/kotoba-brand.woff2').read_bytes()).decode()
 latin=base64.b64encode((ROOT/'static/fonts/kotoba-brand-latin.woff2').read_bytes()).decode()
 css=(ROOT/'static/css/ui-shell.css').read_text()
 css+='\n'+(ROOT/'static/css/liquid-glass.css').read_text()
 css='@font-face{font-family:"Kotoba Serif";src:url(data:font/woff2;base64,'+latin+');font-weight:200 900;font-display:block;}\n@font-face{font-family:"Kotoba Brand";src:url(data:font/woff2;base64,'+font+');font-display:block;}\n'+css
 css='@font-face{font-family:"Kotoba Mincho";src:url(data:font/woff2;base64,'+font+');font-display:block;}\n'+css
 css+='html,body{margin:0;background:#101419;--paper:#111B2B;--card-bg:#1D2B40;--surface:#1B283B;--line:#425169;--ink:#F5EFE5;--serif-jp:"Kotoba Mincho",serif;--serif-body:Arial,sans-serif;}[hidden]{display:none!important;}'
 script="""document.getElementById('kotoba-intro-skip').onclick=function(){KotobaStartupNative.skipIntro();this.hidden=true;if(document.getAnimations)document.getAnimations().forEach(function(a){try{var n=a.effect.getComputedTiming().endTime;if(isFinite(n))a.currentTime=n;else a.pause();}catch(_){}});};"""
 restore="try{if(localStorage.getItem('kotoba:liquid-glass')==='off')document.documentElement.setAttribute('data-glass','off');}catch(_){}"
 html='<!doctype html><html lang="en" data-ui-shell="immersive" data-glass="on"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kotoba intro</title><script>'+restore+'</script><style>'+css+'</style></head><body>'+markup+'<script>'+script+'</script></body></html>'
 destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(html)

if __name__=='__main__':write_opening_asset(ROOT/'android/app/src/main/assets/kotoba-opening.html')
