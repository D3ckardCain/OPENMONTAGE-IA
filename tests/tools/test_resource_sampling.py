from types import SimpleNamespace

from lib import resource_sampling


def test_sampler_records_host_and_gpu_peaks_without_attributing_them_to_project(monkeypatch):
    values=iter([1000,1400,1200])
    monkeypatch.setattr(resource_sampling,'host_ram_mb',lambda:next(values))
    monkeypatch.setattr(resource_sampling,'nvidia_vram_mb',lambda exe:500 if exe else None)
    monkeypatch.setattr(resource_sampling.shutil,'which',lambda name:'nvidia-smi')
    sampler=resource_sampling.ResourceSampler(interval=3600)
    sampler.start();sampler.sample();sampler.sample();result=sampler.finish()
    assert result['host_ram_peak_mb']==1400
    assert result['gpu_vram_peak_mb']==500 and result['samples']==3
    assert 'not_project_attribution' in result['scope']


def test_missing_gpu_or_bad_output_does_not_invent_vram(monkeypatch):
    assert resource_sampling.nvidia_vram_mb(None) is None
    monkeypatch.setattr(resource_sampling.subprocess,'run',lambda *args,**kwargs:
                        SimpleNamespace(returncode=0,stdout='not a number',stderr=''))
    assert resource_sampling.nvidia_vram_mb('nvidia-smi') is None
