import pytest
from lib.translation_segments import segments

class Tokenizer:
    def encode(self,text,**kwargs):return list(text)+['eos']

@pytest.mark.parametrize('text',['Una frase. Otra frase.\nUn párrafo largo. '*30,'한국어 텍스트입니다。 '*80,'x'*1800,'  texto con espacios  \n\n más texto  '])
def test_segments_preserve_every_character_and_positions(text):
    chunks=segments(text,Tokenizer(),'<2es> ',limit=40)
    assert ''.join(chunk['text'] for chunk in chunks)==text
    for index,chunk in enumerate(chunks):
        assert chunk['index']==index
        assert text[chunk['start']:chunk['end']]==chunk['text']
        assert len(Tokenizer().encode('<2es> '+chunk['text']))<=40
    assert chunks[-1]['end']==len(text)


def test_segment_limit_and_impossible_prefix_fail_without_silent_loss():
    with pytest.raises(ValueError):segments('x'*100,Tokenizer(),'prefix',limit=10,max_segments=2)
    with pytest.raises(ValueError):segments('x',Tokenizer(),'too long prefix',limit=3)
    with pytest.raises(ValueError):segments(' ',Tokenizer(),'prefix')
