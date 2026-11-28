"""Excluded tools must not probe runtimes when discovering one capability."""
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backlot.studio_routes import create_studio_router
from tools.base_tool import ToolStatus, ToolRuntime, ToolTier


def entry(name, capability, local=True):
    tool = Mock(name=name)
    tool.name, tool.capability = name, capability
    tool.runtime = ToolRuntime.LOCAL if local else ToolRuntime.API
    tool.tier = ToolTier.ANALYZE
    tool.install_instructions = ''
    tool.get_status.return_value = ToolStatus.AVAILABLE
    return tool


def test_filters_run_before_status_and_preserve_default_response():
    selected = entry('freecad_units', 'cad_parameter_analysis')
    other = entry('qgis_coordinates', 'geographic_coordinate_analysis')
    remote = entry('paid', 'cad_parameter_analysis', local=False)
    registry = Mock(_tools={t.name: t for t in (selected, other, remote)})
    app = FastAPI()
    app.include_router(create_studio_router())
    with patch('tools.tool_registry.registry', registry), TestClient(app) as client:
        response = client.get('/api/studio/tools?name=freecad_units')
        assert response.status_code == 200
        assert [row['name'] for row in response.json()] == ['freecad_units']
        other.get_status.assert_not_called()
        remote.get_status.assert_not_called()
        selected.get_status.reset_mock()
        assert client.get('/api/studio/tools?capability=geographic_coordinate_analysis').json()[0]['name'] == 'qgis_coordinates'
        selected.get_status.assert_not_called()
        assert client.get('/api/studio/tools?name=missing').json() == []
        assert client.get('/api/studio/tools?name=freecad_units&capability=geographic_coordinate_analysis').json() == []
        assert len(client.get('/api/studio/tools').json()) == 2
        remote.get_status.assert_not_called()
        assert client.get('/api/studio/tools?name=' + 'x' * 101).status_code == 422
