"""Lossless source segmentation using the loaded local tokenizer."""
import re


def segments(text,tokenizer,prefix,limit=512,max_segments=128):
    if not isinstance(text,str) or not text.strip():raise ValueError('Indica texto para traducir')
    result=[];offset=0
    def fits(value):return len(tokenizer.encode(prefix+value,add_special_tokens=True))<=limit
    while offset<len(text):
        if len(result)>=max_segments:raise ValueError('El texto supera el máximo de 128 fragmentos; divídelo en varios trabajos')
        remaining=text[offset:]
        if fits(remaining):end=len(remaining)
        else:
            low,high=1,len(remaining);end=0
            while low<=high:
                middle=(low+high)//2
                if fits(remaining[:middle]):end=middle;low=middle+1
                else:high=middle-1
            if not end:raise ValueError('No cabe un fragmento con el prefijo del idioma; revisa el tokenizer')
            # Prefer sentence, paragraph or word boundaries near the limit.
            boundaries=[match.end() for match in re.finditer(r'(?:[.!?。！？]\s+|\n+|\s+)',remaining[:end]) if match.end()>=max(1,end//2)]
            for boundary in reversed(boundaries):
                if fits(remaining[:boundary]):end=boundary;break
        chunk=remaining[:end]
        if not fits(chunk):raise ValueError('No se pudo preparar un fragmento sin truncar')
        result.append({'index':len(result),'start':offset,'end':offset+end,'text':chunk})
        offset+=end
    return result
