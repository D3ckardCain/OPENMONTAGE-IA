"""On-demand public FIFA website feeds; undocumented, no persistent cache."""
import json
import math
import re
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirección FIFA no admitida')


class Transport:
    def get(self, url):
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname not in {'api.fifa.com', 'fdh-api.fifa.com'} or parsed.username or parsed.port:
            raise ValueError('Servicio FIFA no permitido')
        request = urllib.request.Request(url, headers={
            'User-Agent': 'OpenMontageSports/0.1', 'Accept': 'application/json',
            'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=25) as response:
            raw = response.read(12_000_001)
            if len(raw) > 12_000_000:
                raise ValueError('Respuesta FIFA excesiva')
            data = json.loads(raw)
            return data, {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                          'http_date': response.headers.get('Date'), 'http_age': response.headers.get('Age')}


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{1,12}', value):
        raise ValueError('ID FIFA inválido')
    return value


class FIFA:
    def __init__(self, transport=None):
        self.transport = transport or Transport()

    def get(self, path):
        return self.transport.get('https://api.fifa.com/api/v3/' + path)

    @staticmethod
    def pack(kind, scope, rows, requests):
        return {'source': 'FIFA', 'type': kind, 'scope': scope, 'records': rows,
                'queries': requests, 'persistent_cache': False, 'global_coverage': False,
                'warning': 'Servicios públicos no documentados. Consulta nueva; no garantiza actualización instantánea. Cobertura limitada a la edición devuelta; no acredita carrera completa.'}

    def seasons(self, competition_id):
        competition_id = identifier(competition_id)
        data, query = self.get('seasons?' + urlencode({'IdCompetition': competition_id, 'count': 100}))
        if not isinstance(data, dict) or not isinstance(data.get('Results'), list):
            raise ValueError('Listado de ediciones FIFA inválido')
        if data.get('ContinuationToken') or data.get('ContinuationHash'):
            raise ValueError('Ediciones paginadas: no publicar una lista incompleta')
        rows = data['Results']
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or row.get('IdCompetition') != competition_id:
                raise ValueError('FIFA devolvió otra competición')
            key = identifier(row.get('IdSeason'))
            if key in seen:
                raise ValueError('Edición duplicada')
            seen.add(key)
        return self.pack('seasons', {'competition_id': competition_id}, rows, [query])

    def scope(self, competition_id, season_id):
        competition_id = identifier(competition_id)
        season_id = identifier(season_id)
        data, query = self.get('seasons/' + season_id)
        if not isinstance(data, dict) or data.get('IdSeason') != season_id or data.get('IdCompetition') != competition_id:
            raise ValueError('La edición no coincide con la competición solicitada')
        # FDH may use a distinct identity. Never assume the v3 ID is interchangeable.
        fdh_id = identifier((data.get('Properties') or {}).get('IdIFES'))
        return {'competition_id': competition_id, 'season_id': season_id, 'fdh_season_id': fdh_id,
                'season_name': data.get('Name'), 'start_date': data.get('StartDate'),
                'end_date': data.get('EndDate'), 'phase': 'season_aggregate_as_published'}, query

    def teams(self, competition_id, season_id):
        scope, query = self.scope(competition_id, season_id)
        data, source = self.get('competitions/teams/' + season_id)
        if not isinstance(data, dict) or not isinstance(data.get('Results'), list) or data.get('ContinuationToken') or data.get('ContinuationHash'):
            raise ValueError('Equipos incompletos o formato inesperado')
        seen = set()
        for row in data['Results']:
            if not isinstance(row, dict): raise ValueError('Equipo inválido')
            key = identifier(row.get('IdTeam'))
            if key in seen: raise ValueError('Equipo duplicado')
            seen.add(key)
        return self.pack('teams', scope, data['Results'], [query, source])

    def player_statistics(self, competition_id, season_id, player_ids=None, metrics=None):
        if player_ids is not None:
            if not 1 <= len(player_ids) <= 10 or len(set(player_ids)) != len(player_ids):
                raise ValueError('Seleccionar entre uno y diez jugadores distintos')
            for item in player_ids: identifier(item)
        if metrics is not None:
            if not 1 <= len(metrics) <= 30 or len(set(metrics)) != len(metrics) or any(not isinstance(m, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9]{0,99}', m) for m in metrics):
                raise ValueError('Métricas inválidas')
        scope, query = self.scope(competition_id, season_id)
        url = 'https://fdh-api.fifa.com/v1/stats/season/' + scope['fdh_season_id'] + '/players.json'
        data, source = self.transport.get(url)
        if not isinstance(data, dict) or not data:
            raise ValueError('Estadísticas FIFA vacías o formato inesperado')
        parsed = {}
        for pid, stats in data.items():
            identifier(pid)
            if not isinstance(stats, list): raise ValueError('Estadísticas no estructuradas')
            values = {}
            for item in stats:
                if not isinstance(item, list) or len(item) != 3 or not isinstance(item[0], str) or item[0] in values or type(item[2]) is not bool:
                    raise ValueError('Métrica duplicada o formato inesperado')
                value = item[1]
                if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                    raise ValueError('Valor no numérico')
                # Preserve source flag without guessing what it means.
                values[item[0]] = {'value': value, 'source_flag': item[2], 'unit': None}
            parsed[pid] = values
        requested = player_ids or list(parsed)
        if any(pid not in parsed for pid in requested):
            raise ValueError('Jugador ausente de la edición; no sustituir por cero')
        rows = []
        for pid in requested:
            values = parsed[pid]
            selected = metrics or list(values)
            rows.append({'entity_id': pid, 'identity_namespace': 'FIFA_FDH', 'name': None,
                         'statistics': {m: values.get(m, {'value': None, 'source_flag': None, 'unit': None}) for m in selected},
                         'missing_metrics': [m for m in selected if m not in values or values[m]['value'] is None]})
        scope['requested_metrics'] = metrics
        report = self.pack('player_statistics', scope, rows, [query, source])
        report['identity_warning'] = 'Este feed contiene IDs FDH, no nombres. Resolver identidad con evidencia oficial; no asumir equivalencia con IDs de otras fuentes. Unidades no documentadas permanecen null.'
        return report
