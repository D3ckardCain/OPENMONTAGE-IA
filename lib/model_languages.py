"""Language bindings implemented by local speech adapters; not quality claims."""
from pathlib import Path

QWEN={'en':'English','es':'Spanish','zh':'Chinese','ja':'Japanese','ko':'Korean','de':'German','fr':'French','ru':'Russian','pt':'Portuguese','it':'Italian'}
KOKORO={'en':'a','es':'e','fr':'f','hi':'h','it':'i','pt':'p','ja':'j','zh':'z'}


def binding(family,language):
    if not isinstance(language,str) or not language.strip():raise ValueError('Indica el idioma objetivo')
    value=language.strip().lower().replace('_','-');base=value.split('-')[0]
    if family in ('qwen-tts','voice-design','aligner'):
        named={name.lower():name for name in QWEN.values()}
        if value in named:return named[value]
        if base in QWEN:return QWEN[base]
        raise ValueError('Idioma sin correspondencia en este adaptador Qwen: '+language)
    if family=='kokoro':
        if value in set(KOKORO.values())|{'b'}:return value
        if value=='en-gb':return 'b'
        if base in KOKORO:return KOKORO[base]
        raise ValueError('Idioma sin correspondencia en este adaptador Kokoro: '+language)
    return None


def validate_request(family,data):
    if family not in ('kokoro','qwen-tts','voice-design','aligner'):return
    language=data.get('language','en' if family=='kokoro' else '')
    target=binding(family,language)
    if family=='kokoro':
        voice=Path(data.get('voice','af_heart')).stem
        if not voice or voice[0]!=target:
            raise ValueError('La voz Kokoro '+voice+' no corresponde al idioma '+language+'; selecciona una voz local con prefijo '+target)
