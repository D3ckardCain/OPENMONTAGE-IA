import io
import pytest
from PIL import Image
from lib.studio_color import histogram


def test_split_frame_exact_bins_and_extremes_not_clipping_claim():
    image=Image.new('RGB',(4,2));image.paste((0,8,255),(0,0,2,2));image.paste((255,128,0),(2,0,4,2));buffer=io.BytesIO();image.save(buffer,format='PNG')
    result=histogram(buffer.getvalue())
    assert result['before']['rgb_bins_32']['red'][0]==4
    assert result['before']['rgb_bins_32']['green'][1]==4
    assert result['after']['rgb_bins_32']['red'][31]==4
    assert result['after']['rgb_bins_32']['green'][16]==4
    assert result['before']['channel_at_255']['blue']==4
    assert all(sum(v)==4 for side in ['before','after'] for v in result[side]['rgb_bins_32'].values())
    assert result['includes_padding'] and 'do not prove clipping' in result['scope']


def test_histogram_pixel_budget():
    image=Image.new('RGB',(962,2));buffer=io.BytesIO();image.save(buffer,format='PNG')
    with pytest.raises(ValueError,match='presupuesto'):histogram(buffer.getvalue())
