"""Optional Firebase sync. Local writes and startup never wait for the internet.

Only public project configuration is bundled. Anonymous-user credentials and
pending snapshots stay in private learner storage and never in normal backups.
"""
import copy
import hashlib
import json
import re
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SETTINGS = {'kotoba:theme', 'kotoba:daily-goal-minutes', 'kotoba:sound',
            'kotoba:haptics', 'kotoba:voice-search-language'}
MAX_PAYLOAD = 750_000


def clean_settings(value):
    if not isinstance(value, dict):
        raise ValueError('Invalid settings')
    return {k: v for k, v in value.items() if k in SETTINGS and isinstance(v, str) and len(v) <= 200}


def digest(payload):
    stable = {k: v for k, v in payload.items() if k != 'created'}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return copy.deepcopy(default)


class RemoteError(Exception):
    def __init__(self, code=0):
        self.code = code


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request_json(method, url, payload=None, token=None, form=False):
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    body = None
    if payload is not None:
        body = (urllib.parse.urlencode(payload) if form else json.dumps(payload)).encode()
        headers['Content-Type'] = 'application/x-www-form-urlencoded' if form else 'application/json'
    req = urllib.request.Request(url, body, headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=6) as response:
            raw = response.read(1_100_001)
            if len(raw) > 1_100_000:
                raise RemoteError(413)
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raise RemoteError(error.code) from None
    except (OSError, ValueError):
        raise RemoteError() from None


class Firebase:
    def __init__(self, config, directory, atomic):
        self.config, self.directory, self.atomic = config, Path(directory), atomic
        self.path = self.directory / 'cloud_identity.json'
        self.identity = read_json(self.path, {})
        self.token, self.expires = '', 0

    def authenticate(self):
        if self.token and time.time() < self.expires:
            return
        key = urllib.parse.quote(self.config['api_key'], safe='')
        old = self.identity
        if old:
            # An expired/invalid identity must never silently become a new user.
            out = request_json('POST', 'https://securetoken.googleapis.com/v1/token?key=' + key,
                               {'grant_type': 'refresh_token', 'refresh_token': old['refresh_token']}, form=True)
            uid, token, refresh, expires = out['user_id'], out['id_token'], out['refresh_token'], out['expires_in']
            if uid != old['uid'] or old['project_id'] != self.config['project_id']:
                raise RemoteError(401)
        else:
            out = request_json('POST', 'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=' + key,
                               {'returnSecureToken': True})
            uid, token, refresh, expires = out['localId'], out['idToken'], out['refreshToken'], out['expiresIn']
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', uid):
            raise RemoteError(401)
        self.identity = {'uid': uid, 'refresh_token': refresh, 'project_id': self.config['project_id']}
        self.atomic(self.path, self.identity)
        self.token, self.expires = token, time.time() + max(0, int(expires) - 60)

    def url(self, profile):
        uid = self.identity['uid']
        project = self.config['project_id']
        return f'https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents/kotobaUsers/{uid}/profiles/{profile}'

    def get(self, profile):
        try:
            out = request_json('GET', self.url(profile), token=self.token)
        except RemoteError as error:
            if error.code == 404:
                return None
            raise
        payload = json.loads(out['fields']['payload']['stringValue'])
        return {'version': out['updateTime'], 'payload': payload}

    def put(self, profile, payload, version):
        text = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        if len(text.encode()) > MAX_PAYLOAD:
            raise RemoteError(413)
        condition = {'currentDocument.updateTime': version} if version else {'currentDocument.exists': 'false'}
        out = request_json('PATCH', self.url(profile) + '?' + urllib.parse.urlencode(condition),
                           {'fields': {'payload': {'stringValue': text}}}, self.token)
        return out['updateTime']

    def delete(self, profile):
        try:
            request_json('DELETE', self.url(profile), token=self.token)
        except RemoteError as error:
            if error.code != 404:
                raise


class SyncManager:
    def __init__(self, directory, config_path, atomic, state_lock, apply_remote, validate, transport=None):
        self.directory, self.atomic = Path(directory), atomic
        self.path = self.directory / 'cloud_sync_state.json'
        self.config = read_json(config_path, {})
        self.configured = bool(self.config.get('enabled') is True and
                               re.fullmatch(r'[a-z][a-z0-9-]{4,62}', str(self.config.get('project_id', ''))) and
                               re.fullmatch(r'[A-Za-z0-9_-]{10,256}', str(self.config.get('api_key', ''))))
        self.state = read_json(self.path, {'enabled': False, 'profiles': {}})
        if not isinstance(self.state, dict) or not isinstance(self.state.get('profiles'), dict):
            self.state = {'enabled': False, 'profiles': {}}
        self.state['enabled'] = self.state.get('enabled') is True
        self.state['profiles'] = {k: v for k, v in self.state['profiles'].items()
                                  if re.fullmatch(r'device|legacy-[0-9]+', k) and isinstance(v, dict)}
        self.state_lock, self.lock = state_lock, threading.RLock()
        self.apply_remote, self.validate = apply_remote, validate
        self.transport = transport or Firebase(self.config, directory, atomic)
        self.event, self.worker, self.active = threading.Event(), None, 'device'
        self.status, self.last_error = 'local', ''
        self.epoch = 0

    def persist(self):
        self.atomic(self.path, self.state)

    def enable(self, enabled):
        with self.lock:
            if enabled and not self.configured:
                raise ValueError('Cloud sync is not available in this build. Progress stays saved on this device.')
            self.state['enabled'] = bool(enabled)
            self.epoch += 1
            if enabled:
                # Re-enabling explicitly allows recreating a removed cloud copy.
                for entry in self.state['profiles'].values():
                    entry.pop('synced_hash', None)
                    entry.pop('version', None)
            self.persist()

    def observe(self, profile, payload, settings=None):
        if not self.configured or not self.state.get('enabled'):
            return
        with self.lock:
            self.active = profile
            entry = self.state['profiles'].setdefault(profile, {})
            payload = copy.deepcopy(payload)
            payload['browser_settings'] = clean_settings(settings) if settings is not None else entry.get('payload', {}).get('browser_settings', {})
            if digest(payload) != entry.get('hash'):
                entry.update(payload=payload, hash=digest(payload), revision=entry.get('revision', 0) + 1)
                self.persist()
                self.event.set()

    def public_status(self):
        with self.lock:
            entry = self.state['profiles'].get(self.active, {})
            return {'configured': self.configured, 'enabled': bool(self.state.get('enabled')),
                    'state': self.status if self.configured and self.state.get('enabled') else 'local',
                    'pending': entry.get('hash') != entry.get('synced_hash'),
                    'last_synced': entry.get('last_synced'), 'message': self.last_error,
                    'profile': self.active,
                    'remote_settings_version': entry.get('settings_revision', ''),
                    'remote_settings': entry.get('remote_settings', {})}

    def export_connection(self, profile):
        identity = self.transport.identity
        if not self.configured or not identity.get('refresh_token'):
            raise ValueError('Enable cloud sync and connect to internet once before saving a private cloud key.')
        with self.lock:
            entry = self.state['profiles'].get(profile, {})
            return {'format': 'kotoba-cloud-key-v1', 'project_id': identity['project_id'],
                    'uid': identity['uid'], 'refresh_token': identity['refresh_token'],
                    'profile': entry.get('remote_profile', profile)}

    def connect(self, connection, profile, local_payload):
        if not self.configured:
            raise ValueError('Cloud sync is not available in this build.')
        if not isinstance(connection, dict) or connection.get('format') != 'kotoba-cloud-key-v1':
            raise ValueError('Choose a private Kotoba cloud key file.')
        if connection.get('project_id') != self.config['project_id']:
            raise ValueError('This cloud key belongs to a different Kotoba service.')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', str(connection.get('uid', ''))) or not re.fullmatch(r'device|legacy-[0-9]+', str(connection.get('profile', ''))):
            raise ValueError('Invalid cloud key.')
        token = connection.get('refresh_token')
        if not isinstance(token, str) or not 10 <= len(token) <= 8192:
            raise ValueError('Invalid cloud key.')
        candidate = Firebase(self.config, self.directory, lambda *args: None)
        candidate.identity = {k: connection[k] for k in ['uid', 'project_id', 'refresh_token']}
        # Validate before replacing any existing identity. No new anonymous user.
        candidate.authenticate()
        with self.state_lock, self.lock:
            self.epoch += 1
            candidate.atomic = self.atomic
            self.atomic(candidate.path, candidate.identity)
            self.transport = candidate
            self.state = {'enabled': True, 'profiles': {}}
            self.active = profile
            self.observe(profile, local_payload)
            self.state['profiles'][profile].update(remote_profile=connection['profile'], force_cloud_once=True)
            self.persist()
            self.event.set()
        self.start()

    def start(self):
        if not self.configured or not self.state.get('enabled'):
            return
        with self.lock:
            if self.worker and self.worker.is_alive():
                return
            self.worker = threading.Thread(target=self.run, name='KotobaCloudSync', daemon=True)
            self.worker.start()

    def request_delete(self, profile):
        if not self.configured:
            raise ValueError('Cloud sync is not available in this build.')
        with self.lock:
            self.active = profile
            self.state['profiles'].setdefault(profile, {})['delete_requested'] = True
            self.state['enabled'] = True
            self.epoch += 1
            self.status = 'waiting'
            self.last_error = 'Cloud deletion is queued. Local progress is kept; internet is needed to delete the cloud copy.'
            self.persist()
            self.event.set()
        self.start()

    def run(self):
        delay = 60
        while self.state.get('enabled'):
            changed = self.event.wait(delay)
            self.event.clear()
            # Collapse rapid answer/settings writes into a single snapshot.
            if changed:
                self.event.wait(2)
                self.event.clear()
            self.step()
            delay = min(delay * 2, 120) if self.status == 'waiting' else 60

    def step(self):
        with self.lock:
            if not self.configured or not self.state.get('enabled'):
                return
            profile = self.active
            epoch = self.epoch
            entry = copy.deepcopy(self.state['profiles'].get(profile, {}))
            remote_profile = entry.get('remote_profile', profile)
            if not entry.get('payload') and not entry.get('delete_requested'):
                return
            self.status, self.last_error = 'syncing', ''
        try:
            self.transport.authenticate()
            if entry.get('delete_requested'):
                self.transport.delete(remote_profile)
                with self.lock:
                    if self.epoch == epoch:
                        current = self.state['profiles'][profile]
                        current.pop('delete_requested', None)
                        current.pop('version', None)
                        current.pop('synced_hash', None)
                        current.pop('conflict', None)
                        self.state['enabled'] = False
                        self.status, self.last_error = 'local', 'Cloud copy deleted. Sync is off; local progress is kept.'
                        self.persist()
                return
            remote = self.transport.get(remote_profile)
            if remote:
                self.validate(remote['payload'])
                remote_hash = digest(remote['payload'])
                version = remote['version']
            else:
                remote_hash, version = None, None
            # Always acquire the learner lock before the manager lock.
            with self.state_lock, self.lock:
                if not self.state.get('enabled') or self.epoch != epoch:
                    return
                current = self.state['profiles'][profile]
                if current.get('delete_requested'):
                    return
                if current['revision'] != entry['revision']:
                    self.status = 'waiting'
                    return
                dirty = current['hash'] != current.get('synced_hash')
                if remote_hash == current['hash']:
                    current.update(version=version, synced_hash=current['hash'], last_synced=time.time())
                    self.status = 'synced'
                    self.persist()
                    return
                changed = version != current.get('version')
                if remote and changed and dirty and not current.get('force_cloud_once'):
                    current['conflict'] = remote
                    self.status = 'conflict'
                    self.persist()
                    return
                if remote and changed and (not dirty or current.get('force_cloud_once')):
                    self.apply_remote(profile, remote['payload'])
                    settings = clean_settings(remote['payload'].get('browser_settings', {}))
                    current.update(payload=remote['payload'], hash=remote_hash, synced_hash=remote_hash,
                                   version=version, last_synced=time.time(), remote_settings=settings)
                    current['settings_revision'] = secrets.token_hex(10)
                    current.pop('force_cloud_once', None)
                    self.status = 'synced'
                    self.persist()
                    return
                if not remote and current.get('version'):
                    # A cloud deletion must not recreate data from another device.
                    self.status, self.last_error = 'deleted', 'Cloud copy was removed. Local progress is kept. Turn sync off and on to save a new cloud copy.'
                    return
            new_version = self.transport.put(remote_profile, entry['payload'], version)
            with self.lock:
                if self.epoch != epoch:
                    return
                current = self.state['profiles'][profile]
                current.update(version=new_version, synced_hash=entry['hash'], last_synced=time.time())
                current.pop('force_cloud_once', None)
                self.status = 'synced' if current['hash'] == entry['hash'] else 'waiting'
                self.persist()
        except RemoteError as error:
            with self.lock:
                self.status = 'waiting'
                if error.code in {409, 412}:
                    self.last_error = 'Cloud changed during sync. Checking again; local progress is safe.'
                elif error.code == 413:
                    self.last_error = 'Progress is too large for cloud sync. Export a backup; local progress is saved.'
                elif error.code in {400, 401, 403}:
                    self.last_error = 'Cloud connection needs attention. Local progress is saved.'
                    self.transport.token = ''
                else:
                    self.last_error = 'Waiting for internet or cloud service. Progress is saved on this device.'
        except (OSError, ValueError, KeyError, TypeError):
            with self.lock:
                self.status, self.last_error = 'waiting', 'Could not sync. Local progress is saved; export a backup if needed.'

    def resolve(self, choice):
        with self.state_lock, self.lock:
            current = self.state['profiles'].get(self.active, {})
            remote = current.get('conflict')
            if not remote or choice not in {'local', 'cloud'}:
                raise ValueError('No matching cloud conflict')
            if choice == 'cloud':
                self.validate(remote['payload'])
                self.apply_remote(self.active, remote['payload'])
                current.update(payload=remote['payload'], hash=digest(remote['payload']), synced_hash=digest(remote['payload']))
                current['remote_settings'] = clean_settings(remote['payload'].get('browser_settings', {}))
                current['settings_revision'] = secrets.token_hex(10)
            current['version'] = remote['version']
            current.pop('conflict', None)
            current['revision'] += 1
            self.persist()
            self.status = 'waiting'
            self.event.set()
