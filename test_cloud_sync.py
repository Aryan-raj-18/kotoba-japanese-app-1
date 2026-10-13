"""Offline durability, cloud retries and conflicts using a simulated provider.

These checks do not claim a connection to a live Firebase project.
"""
import copy
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ['KOTOBA_DATA_DIR'] = tempfile.mkdtemp(prefix='kotoba-cloud-test-')
if os.environ.get('KOTOBA_TEST_PACKAGE'):
    sys.path.insert(0, os.environ['KOTOBA_TEST_PACKAGE'])
    import kotoba_app.app as K
else:
    import app as K
C = K._cloud


class FakeCloud:
    def __init__(self):
        self.remote = None
        self.online = True
        self.writes = []
        self.token = 'simulated'
        self.counter = 0

    def authenticate(self):
        if not self.online:
            raise C.RemoteError()

    def get(self, profile):
        return copy.deepcopy(self.remote)

    def put(self, profile, payload, version):
        if (self.remote or {}).get('version') != version:
            raise C.RemoteError(412)
        self.counter += 1
        self.remote = {'version': str(self.counter), 'payload': copy.deepcopy(payload)}
        self.writes.append((profile, copy.deepcopy(payload)))
        return str(self.counter)

    def delete(self, profile):
        if not self.online:
            raise C.RemoteError()
        self.remote = None


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.config = self.directory / 'config.json'
        self.config.write_text(json.dumps({'enabled': True, 'project_id': 'kotoba-test', 'api_key': 'SIMULATED_API_KEY'}))
        self.provider = FakeCloud()
        self.applied = []
        self.local = {'format': 'kotoba-backup-v1', 'learner': {'xp': 10}, 'created': 'initial'}
        self.manager = self.new_manager()
        self.manager.enable(True)
        self.manager.observe('device', self.local)

    def tearDown(self):
        self.temp.cleanup()

    def new_manager(self):
        def validate(payload):
            if not isinstance(payload, dict) or type(payload.get('learner', {}).get('xp')) is not int:
                raise ValueError('Invalid cloud copy')
        return C.SyncManager(self.directory, self.config, K._safety.atomic_json, threading.RLock(),
                             lambda profile, payload: self.applied.append(copy.deepcopy(payload)), validate, self.provider)

    def test_offline_queue_survives_process_recreation(self):
        self.provider.online = False
        self.manager.step()
        self.assertEqual(self.manager.public_status()['state'], 'waiting')
        restarted = self.new_manager()
        self.assertTrue(restarted.public_status()['pending'])
        self.provider.online = True
        restarted.step()
        self.assertEqual(self.provider.remote['payload']['learner']['xp'], 10)

    def test_changes_coalesce_to_latest_snapshot(self):
        self.manager.observe('device', {**self.local, 'learner': {'xp': 20}})
        self.manager.observe('device', {**self.local, 'learner': {'xp': 30}})
        self.manager.step()
        self.assertEqual(len(self.provider.writes), 1)
        self.assertEqual(self.provider.writes[0][1]['learner']['xp'], 30)

    def test_repeated_sync_does_not_write_duplicate_copy(self):
        self.manager.step()
        for _ in range(3):
            self.manager.observe('device', {**self.local, 'created': 'later'})
            self.manager.step()
        self.assertEqual(len(self.provider.writes), 1)

    def test_cloud_update_applies_only_when_local_copy_is_clean(self):
        self.manager.step()
        self.provider.remote = {'version': 'external', 'payload': {**self.local, 'learner': {'xp': 50}}}
        self.manager.step()
        self.assertEqual(self.applied[-1]['learner']['xp'], 50)
        self.assertFalse(self.manager.public_status()['pending'])

    def conflict(self):
        self.manager.step()
        self.manager.observe('device', {**self.local, 'learner': {'xp': 20}})
        self.provider.remote = {'version': 'external', 'payload': {**self.local, 'learner': {'xp': 50}}}
        self.manager.step()

    def test_offline_edits_do_not_overwrite_changed_cloud(self):
        self.conflict()
        self.assertEqual(self.manager.public_status()['state'], 'conflict')
        self.assertFalse(self.applied)
        self.assertEqual(len(self.provider.writes), 1)
        self.assertEqual(self.manager.state['profiles']['device']['payload']['learner']['xp'], 20)

    def test_explicit_local_conflict_choice_uploads_local_copy(self):
        self.conflict()
        self.manager.resolve('local')
        self.manager.step()
        self.assertEqual(self.provider.remote['payload']['learner']['xp'], 20)

    def test_explicit_cloud_conflict_choice_preserves_cloud_copy(self):
        self.conflict()
        self.manager.resolve('cloud')
        self.manager.step()
        self.assertEqual(self.applied[-1]['learner']['xp'], 50)
        self.assertEqual(len(self.provider.writes), 1)

    def test_changed_remote_during_upload_retries_without_marking_clean(self):
        with patch.object(self.provider, 'put', side_effect=C.RemoteError(412)):
            self.manager.step()
        self.assertTrue(self.manager.public_status()['pending'])
        self.assertEqual(self.manager.public_status()['state'], 'waiting')

    def test_invalid_cloud_copy_cannot_replace_local_progress(self):
        self.manager.step()
        self.provider.remote = {'version': 'bad', 'payload': {'learner': {'xp': []}}}
        self.manager.step()
        self.assertFalse(self.applied)
        self.assertEqual(self.manager.state['profiles']['device']['payload']['learner']['xp'], 10)

    def test_disabling_sync_during_remote_read_blocks_restore_and_upload(self):
        with patch.object(self.provider, 'get', side_effect=lambda profile: self.manager.enable(False)):
            self.manager.step()
        self.assertFalse(self.applied)
        self.assertFalse(self.provider.writes)

    def test_local_changes_during_remote_read_are_not_lost(self):
        def reading(profile):
            self.manager.observe('device', {**self.local, 'learner': {'xp': 80}})
            return None
        with patch.object(self.provider, 'get', side_effect=reading):
            self.manager.step()
        self.assertFalse(self.provider.writes)
        self.manager.step()
        self.assertEqual(self.provider.remote['payload']['learner']['xp'], 80)

    def test_removed_cloud_copy_is_not_recreated_without_explicit_enable(self):
        self.manager.step()
        self.provider.remote = None
        self.manager.step()
        self.assertEqual(self.manager.public_status()['state'], 'deleted')
        self.assertEqual(len(self.provider.writes), 1)
        self.manager.enable(False)
        self.manager.enable(True)
        self.manager.step()
        self.assertEqual(len(self.provider.writes), 2)

    def test_offline_changes_cannot_resurrect_deleted_remote_copy(self):
        self.manager.step()
        self.manager.observe('device', {**self.local, 'learner': {'xp': 25}})
        self.provider.remote = None
        self.manager.step()
        self.assertEqual(self.manager.public_status()['state'], 'deleted')
        self.assertEqual(len(self.provider.writes), 1)
        self.assertTrue(self.manager.public_status()['pending'])

    def test_private_settings_are_not_part_of_cloud_payload(self):
        self.manager.observe('device', self.local, {'kotoba:theme': 'fuji-mist', 'kotoba:wallpaper:frame': 'private', 'token': 'secret', 'kotoba:reminder': 'time'})
        self.manager.step()
        self.assertEqual(self.provider.remote['payload']['browser_settings'], {'kotoba:theme': 'fuji-mist'})

    def test_cloud_delete_turns_sync_off_and_keeps_local_snapshot(self):
        self.manager.step()
        with patch.object(self.manager, 'start'):
            self.manager.request_delete('device')
        self.manager.step()
        self.assertIsNone(self.provider.remote)
        self.assertFalse(self.manager.state['enabled'])
        self.assertEqual(self.manager.state['profiles']['device']['payload']['learner']['xp'], 10)

    def test_cloud_delete_survives_offline_process_restart(self):
        self.manager.step()
        self.provider.online = False
        with patch.object(self.manager, 'start'):
            self.manager.request_delete('device')
        self.manager.step()
        restarted = self.new_manager()
        self.assertTrue(restarted.state['profiles']['device']['delete_requested'])
        self.provider.online = True
        restarted.step()
        self.assertIsNone(self.provider.remote)
        self.assertFalse(restarted.state['enabled'])

    def test_exported_key_is_separate_from_normal_progress_payload(self):
        self.provider.identity = {'project_id': 'kotoba-test', 'uid': 'owner', 'refresh_token': 'private-refresh'}
        key = self.manager.export_connection('device')
        self.assertEqual(key['format'], 'kotoba-cloud-key-v1')
        self.assertEqual(key['refresh_token'], 'private-refresh')
        self.assertNotIn('refresh_token', json.dumps(self.manager.state['profiles']['device']['payload']))

    def connection(self):
        return {'format': 'kotoba-cloud-key-v1', 'project_id': 'kotoba-test', 'uid': 'owner',
                'refresh_token': 'private-refresh-token', 'profile': 'legacy-1'}

    def test_failed_key_verification_preserves_existing_connection(self):
        before = copy.deepcopy(self.manager.state)
        with patch.object(C, 'request_json', side_effect=C.RemoteError(400)):
            with self.assertRaises(C.RemoteError):
                self.manager.connect(self.connection(), 'device', self.local)
        self.assertEqual(self.manager.state, before)
        self.assertIs(self.manager.transport, self.provider)

    def test_cloud_key_connects_a_second_device_to_same_remote_profile(self):
        identity = {'user_id': 'owner', 'id_token': 'id', 'refresh_token': 'rotated-private', 'expires_in': '3600'}
        with patch.object(C, 'request_json', return_value=identity), patch.object(self.manager, 'start'):
            self.manager.connect(self.connection(), 'device', self.local)
        self.assertEqual(self.manager.transport.identity['uid'], 'owner')
        self.assertEqual(self.manager.state['profiles']['device']['remote_profile'], 'legacy-1')
        remote = {'version': 'linked', 'payload': {**self.local, 'learner': {'xp': 70}}}
        with patch.object(self.manager.transport, 'get', return_value=remote) as get:
            self.manager.step()
        self.assertEqual(get.call_args.args[0], 'legacy-1')
        self.assertEqual(self.applied[-1]['learner']['xp'], 70)

    def test_cloud_key_from_other_project_is_rejected_without_network(self):
        connection = self.connection()
        connection['project_id'] = 'other-project'
        with patch.object(C, 'request_json') as network:
            with self.assertRaises(ValueError):
                self.manager.connect(connection, 'device', self.local)
        network.assert_not_called()

    def test_firestore_create_and_update_have_preconditions(self):
        provider = C.Firebase({'project_id': 'kotoba-test'}, self.directory, K._safety.atomic_json)
        provider.identity, provider.token = {'uid': 'owner'}, 'ID_TOKEN'
        with patch.object(C, 'request_json', return_value={'updateTime': 'next'}) as req:
            provider.put('device', self.local, None)
            self.assertIn('currentDocument.exists=false', req.call_args.args[1])
            provider.put('device', self.local, 'previous')
            self.assertIn('currentDocument.updateTime=previous', req.call_args.args[1])

    def test_expired_identity_refreshes_without_changing_user(self):
        provider = C.Firebase({'project_id': 'kotoba-test', 'api_key': 'PUBLIC_API_KEY'}, self.directory, K._safety.atomic_json)
        provider.identity = {'uid': 'owner', 'refresh_token': 'private', 'project_id': 'kotoba-test'}
        out = {'user_id': 'owner', 'id_token': 'new-id', 'refresh_token': 'new-refresh', 'expires_in': '3600'}
        with patch.object(C, 'request_json', return_value=out) as req:
            provider.authenticate()
        self.assertIn('securetoken.googleapis.com', req.call_args.args[1])
        self.assertEqual(json.loads(provider.path.read_text())['uid'], 'owner')

    def test_invalid_identity_is_not_replaced_by_new_anonymous_user(self):
        provider = C.Firebase({'project_id': 'kotoba-test', 'api_key': 'PUBLIC_API_KEY'}, self.directory, K._safety.atomic_json)
        provider.identity = {'uid': 'owner', 'refresh_token': 'private', 'project_id': 'kotoba-test'}
        with patch.object(C, 'request_json', side_effect=C.RemoteError(400)) as req:
            with self.assertRaises(C.RemoteError):
                provider.authenticate()
        self.assertEqual(req.call_count, 1)
        self.assertEqual(provider.identity['uid'], 'owner')

    def test_cloud_size_limit_keeps_local_pending_copy(self):
        provider = C.Firebase({'project_id': 'kotoba-test'}, self.directory, K._safety.atomic_json)
        provider.identity = {'uid': 'owner'}
        with self.assertRaises(C.RemoteError) as error:
            provider.put('device', {'learner': {'text': 'x' * (C.MAX_PAYLOAD + 1)}}, None)
        self.assertEqual(error.exception.code, 413)


class OfflineAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        K.DATA_DIR = Path(self.temp.name)
        for name in dir(K):
            value = getattr(K, name)
            if name.isupper() and name.endswith(('_FILE', '_PATH')) and isinstance(value, Path):
                setattr(K, name, K.DATA_DIR / value.name)
        self.client = K.app.test_client()
        self.client.get('/sync')

    def tearDown(self):
        self.temp.cleanup()

    def test_open_save_reload_and_backup_without_external_network(self):
        with patch.object(C, 'request_json', side_effect=AssertionError('Unexpected internet dependency')):
            for route in ['/', '/sync', '/kanji?level=N4', '/backup', '/api/cloud/status']:
                self.assertEqual(self.client.get(route).status_code, 200)
            self.assertEqual(self.client.post('/api/learner/record', json={'id': 'water', 'front': '水', 'correct': True, 'quality': 4}).status_code, 200)
            fresh = K.app.test_client()
            backup = fresh.get('/api/backup/data').json
            self.assertEqual(backup['learner']['reviews'], 1)
            self.assertNotIn('cloud_identity', backup)
            self.assertNotIn('refresh_token', json.dumps(backup))

    def test_unconfigured_build_reports_truthful_cloud_availability(self):
        out = self.client.get('/api/cloud/status').json
        self.assertFalse(out['configured'])
        self.assertFalse(out['enabled'])
        with self.client.session_transaction() as session:
            csrf = session['csrf_token']
        response = self.client.post('/api/cloud/settings', json={'enabled': True, 'csrf_token': csrf})
        self.assertEqual(response.status_code, 400)
        self.assertIn('not available', response.json['error'])

    def test_cloud_controls_require_app_csrf(self):
        for route, payload in [('/api/cloud/settings', {'enabled': True}), ('/api/cloud/resolve', {'choice': 'cloud', 'confirm': 'REPLACE'}), ('/api/cloud/delete', {'confirm': 'DELETE CLOUD'}), ('/api/cloud/key', {'confirm': 'SAVE KEY'}), ('/api/cloud/connect', {'confirm': 'CONNECT'})]:
            self.assertEqual(self.client.post(route, json=payload).status_code, 400)

    def test_real_progress_copy_is_validated_and_restored_transactionally(self):
        self.client.post('/api/learner/action', json={'action': 'audio'})
        payload = self.client.get('/api/backup/data').json
        payload['learner']['xp'] = 60
        K._apply_cloud_copy('device', payload)
        self.assertEqual(self.client.get('/api/backup/data').json['learner']['xp'], 60)
        self.assertTrue((K.DATA_DIR / 'before_restore_guest.json').exists())
        invalid = copy.deepcopy(payload)
        invalid['learner']['xp'] = []
        with self.assertRaises(ValueError):
            K._apply_cloud_copy('device', invalid)
        self.assertEqual(self.client.get('/api/backup/data').json['learner']['xp'], 60)


if __name__ == '__main__':
    unittest.main(verbosity=2)
