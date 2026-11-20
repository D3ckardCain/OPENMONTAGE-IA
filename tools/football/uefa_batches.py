"""Partition UEFA player metric requests while preserving the source of each value."""
from collections import deque
from decimal import Decimal, InvalidOperation

from tools.football.uefa import UEFAHTTPError, Unavailable


def metric_batches(metrics):
    return deque(metrics[start:start + 8] for start in range(0, len(metrics), 8))


def split_rejected_batch(pending, batch, error):
    if not isinstance(error, UEFAHTTPError) or error.status not in (400, 422, 500) or len(batch) < 2:
        return False
    midpoint = len(batch) // 2
    pending.appendleft(batch[midpoint:])
    pending.appendleft(batch[:midpoint])
    return True


def checked_statistics(items, metrics):
    result = {}
    for item in items:
        metric, value = item['name'], item['value']
        if metric not in metrics or metric in result:
            raise Unavailable('UEFA devolvió una métrica ajena o duplicada en el lote')
        try:
            if value is not None and not Decimal(str(value)).is_finite():
                raise InvalidOperation
        except InvalidOperation:
            raise Unavailable('UEFA devolvió un valor estadístico inválido') from None
        result[metric] = item
    return result
