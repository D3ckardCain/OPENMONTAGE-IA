"""Technical pilots retain planning approval without repeating their renders."""
import pytest

from lib import checkpoint
from tests.contracts.test_phase0_contracts import sample_artifact


@pytest.mark.parametrize('pipeline', ['blender-skills-pilot', 'hyperframes-offline-pilot'])
def test_pilot_requires_approved_idea_before_scene_plan(tmp_path, pipeline):
    checkpoint.init_project('pilot', title='Synthetic planning gate', pipeline_type=pipeline, pipeline_dir=tmp_path)
    scene = {'scene_plan': sample_artifact('scene_plan')}
    with pytest.raises(checkpoint.CheckpointValidationError, match='idea'):
        checkpoint.write_checkpoint(tmp_path, 'pilot', 'scene_plan', 'completed', scene,
                                    pipeline_type=pipeline, human_approved=True)
    brief = {'brief': sample_artifact('brief')}
    with pytest.raises(checkpoint.CheckpointValidationError, match='GATE VIOLATION'):
        checkpoint.write_checkpoint(tmp_path, 'pilot', 'idea', 'completed', brief,
                                    pipeline_type=pipeline)
    checkpoint.write_checkpoint(tmp_path, 'pilot', 'idea', 'completed', brief,
                                pipeline_type=pipeline, human_approved=True)
    checkpoint.write_checkpoint(tmp_path, 'pilot', 'scene_plan', 'completed', scene,
                                pipeline_type=pipeline, human_approved=True)
    assert not list((tmp_path / 'pilot' / 'renders').glob('*'))
