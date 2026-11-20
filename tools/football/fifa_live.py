"""On-demand public FIFA website feeds; undocumented, no persistent cache."""
import json
import math
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
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


    @staticmethod
    def names(values):
        if not isinstance(values, list): raise ValueError('Nombres FIFA inválidos')
        result = []
        for item in values:
            if not isinstance(item, dict) or not isinstance(item.get('Description'), str):
                raise ValueError('Nombre FIFA mal formado')
            if item['Description'].strip(): result.append(item['Description'])
        return result

    @staticmethod
    def normalize(value):
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 150:
            raise ValueError('Nombre requerido, máximo 150 caracteres')
        text = ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))
        return ' '.join(re.findall(r'[^\W_]+', text, re.UNICODE))

    def _squad(self, competition_id, season_id, team_id):
        team_id = identifier(team_id)
        data, query = self.get('teams/' + team_id + '/squad?' + urlencode({
            'idCompetition': competition_id, 'idSeason': season_id}))
        if not isinstance(data, dict) or (data.get('IdCompetition'), data.get('IdSeason'), data.get('IdTeam')) != (competition_id, season_id, team_id):
            raise ValueError('Plantilla pertenece a otro equipo, edición o competición')
        if not isinstance(data.get('Players'), list) or not data['Players']:
            raise ValueError('Plantilla vacía o no estructurada')
        rows = []; seen = set()
        for player in data['Players']:
            if not isinstance(player, dict) or player.get('IdTeam') != team_id or player.get('IdSeason') != season_id:
                raise ValueError('Jugador fuera de la plantilla solicitada')
            pid = identifier(player.get('IdPlayer'))
            if pid in seen: raise ValueError('Jugador duplicado en la plantilla')
            seen.add(pid)
            names = self.names(player.get('PlayerName'))
            if not names: raise ValueError('Jugador sin nombre oficial')
            aliases = names + self.names(player.get('ShortName', []))
            fdh = (player.get('Properties') or {}).get('IdIFES')
            if fdh is not None: identifier(fdh)
            rows.append({'player_id': pid, 'fdh_player_id': fdh, 'name': names[0],
                         'aliases': list(dict.fromkeys(aliases)), 'team_id': team_id,
                         'team_name': data.get('TeamName'), 'country': player.get('IdCountry'),
                         'birth_date': player.get('BirthDate'), 'jersey': player.get('JerseyNum'),
                         'position': player.get('PositionLocalized'), 'identity_source': query})
        return rows, query

    def squad(self, competition_id, season_id, team_id):
        scope, query = self.scope(competition_id, season_id)
        rows, source = self._squad(competition_id, season_id, team_id)
        return self.pack('squad', {**scope, 'team_id': team_id}, rows, [query, source])

    def resolve_players(self, competition_id, season_id, subjects):
        if not isinstance(subjects, list) or not 1 <= len(subjects) <= 10:
            raise ValueError('Indicar entre uno y diez nombres')
        normalized = []
        for subject in subjects:
            if not isinstance(subject, dict) or set(subject) - {'name', 'team_name'}:
                raise ValueError('Sujeto inválido')
            name = self.normalize(subject.get('name'))
            team = self.normalize(subject['team_name']) if subject.get('team_name') else None
            if not name: raise ValueError('Nombre vacío')
            normalized.append((name, team))
        teams = self.teams(competition_id, season_id)
        if not teams['records'] or len(teams['records']) > 64:
            raise ValueError('Lista de equipos vacía o excesiva; no resolver parcialmente')
        selected = set()
        for name, team in normalized:
            matches = [row for row in teams['records'] if team is None or team in {
                self.normalize(n) for n in self.names(row.get('Name')) + [row.get('Abbreviation') or row['IdTeam']]}]
            if not matches: raise ValueError('Equipo solicitado no identificado en la edición')
            selected.update(row['IdTeam'] for row in matches)
        # Bounded network concurrency; one failed squad invalidates the lookup.
        with ThreadPoolExecutor(max_workers=4) as pool:
            squads = list(pool.map(lambda tid: self._squad(competition_id, season_id, tid), sorted(selected)))
        players = [row for rows, query in squads for row in rows]
        results = []
        for subject, (name, team) in zip(subjects, normalized):
            candidates = []
            for row in players:
                if team is not None:
                    original = next(t for t in teams['records'] if t['IdTeam'] == row['team_id'])
                    team_aliases = self.names(original.get('Name')) + [original.get('Abbreviation') or original['IdTeam']]
                    if team not in {self.normalize(n) for n in team_aliases}: continue
                aliases = [self.normalize(n) for n in row['aliases']]
                if any(name == alias or (' ' + name + ' ') in (' ' + alias + ' ') for alias in aliases):
                    candidates.append(row)
            # Never choose the first candidate of an ambiguous surname.
            status = 'resolved' if len(candidates) == 1 else 'ambiguous' if candidates else 'not_found'
            results.append({'requested': subject, 'status': status, 'candidates': candidates})
        return self.pack('player_resolution', teams['scope'], results,
                         teams['queries'] + [query for rows, query in squads])

    def compare_players(self, competition_id, season_id, subjects, metrics):
        if not isinstance(subjects, list) or len(subjects) != 2:
            raise ValueError('La comparativa requiere exactamente dos jugadores')
        identities = self.resolve_players(competition_id, season_id, subjects)
        if any(row['status'] != 'resolved' for row in identities['records']):
            return {**identities, 'type': 'comparison_blocked', 'ready_for_script': False,
                    'reason': 'Identidad ausente o ambigua; no producir cifras atribuidas.'}
        players = [row['candidates'][0] for row in identities['records']]
        ids = [row['fdh_player_id'] for row in players]
        if None in ids or len(set(ids)) != 2:
            raise ValueError('Falta vínculo FDH oficial o se pidió el mismo jugador dos veces')
        stats = self.player_statistics(competition_id, season_id, ids, metrics)
        for row, player in zip(stats['records'], players):
            if row['entity_id'] != player['fdh_player_id']: raise ValueError('Identidad estadística inconsistente')
            row['name'] = player['name']; row['identity'] = player
        stats['queries'] = identities['queries'] + stats['queries']
        stats['type'] = 'player_comparison'
        stats['identity_warning'] = 'Nombres y vínculo FDH obtenidos de las plantillas oficiales de esta edición.'
        stats['ready_for_script'] = not any(row['missing_metrics'] for row in stats['records'])
        return stats

    def collectible_card(self, competition_id, season_id, subjects, metrics):
        """Fresh evidence for one card, not a rendered image or permission grant."""
        if not isinstance(subjects, list) or len(subjects) != 1:
            raise ValueError('La postal requiere exactamente un jugador')
        identities = self.resolve_players(competition_id, season_id, subjects)
        resolved = identities['records'][0]
        if resolved['status'] != 'resolved':
            return {**identities, 'type': 'card_blocked', 'ready_for_script': False,
                    'reason': 'Identidad ausente o ambigua; no crear una postal atribuida.'}
        identity = resolved['candidates'][0]
        if identity['fdh_player_id'] is None:
            raise ValueError('Falta vínculo estadístico FDH oficial')
        stats = self.player_statistics(competition_id, season_id, [identity['fdh_player_id']], metrics)
        record = stats['records'][0]
        source = stats['queries'][-1]
        # No inferred age, career totals, skill rating, trophy count or image rights.
        facts = [{'metric': metric, **value, 'entity_id': record['entity_id'],
                  'scope': stats['scope'].copy(), 'source_url': source['url'],
                  'retrieved_at': source['retrieved_at']} for metric, value in record['statistics'].items()]
        return self.pack('collectible_card', stats['scope'], [{
            'identity': identity, 'facts': facts, 'missing_metrics': record['missing_metrics'],
            'image': None, 'image_rights': 'not_provided', 'career_record': None,
            'skill_rating': None, 'trophies': None}], identities['queries'] + stats['queries']) | {
                'ready_for_script': not record['missing_metrics'], 'rendered': False,
                'usage': 'Datos fechados de una edición para una postal original. No reutilizar como cifras actuales en otra producción. El diseño y las imágenes se preparan después.'}
