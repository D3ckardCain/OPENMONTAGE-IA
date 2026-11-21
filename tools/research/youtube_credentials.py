"""Process-local API key override; never returned to the browser or persisted."""
import os
import threading

SESSION_KEY=None
LOCK=threading.RLock()


def get_key():
    with LOCK:return SESSION_KEY or os.environ.get('YOUTUBE_API_KEY') or None


def status():
    with LOCK:
        source='session' if SESSION_KEY else 'environment' if os.environ.get('YOUTUBE_API_KEY') else None
        return {'configured':source is not None,'source':source,'session_key_persisted':False,
                'key_verified':False,'remaining_quota':None}


def configure(data):
    global SESSION_KEY
    if set(data)!={'api_key'} or not isinstance(data['api_key'],str):raise ValueError('Indica api_key')
    value=data['api_key'].strip()
    if value and (len(value)<20 or len(value)>200 or any(not(c.isascii() and (c.isalnum() or c in '_-')) for c in value)):raise ValueError('Formato de clave inválido')
    with LOCK:SESSION_KEY=value or None
    return status()
