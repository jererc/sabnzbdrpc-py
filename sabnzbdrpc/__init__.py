import json
from urllib import urlencode
import logging

logging.getLogger('requests').setLevel(logging.ERROR)
import requests


logger = logging.getLogger(__name__)


class ApiError(Exception): pass


class Sabnzbd(object):

    def __init__(self, host='localhost', port=8080, api_key=None):
        self.base_url = 'http://%s:%s/api' % (host, port)
        self.api_key = api_key

    def _send(self, **info):
        if self.api_key:
            info['apikey'] = self.api_key
        info['output'] = 'json'

        url = '%s?%s' % (self.base_url, urlencode(info))
        response = requests.get(url)
        if response.status_code != requests.codes.ok:
            raise ApiError('failed to get %s: %s' % (url, response.status_code))
        res = json.loads(response.content)
        if not res.get('status', True):
            raise ApiError('failed to get %s: %s' % (url, res['error']))
        return res

    def add_nzb(self, file, pp=3, priority=0):
        res = self._send(mode='addlocalfile', name=file,
                pp=pp, priority=priority)
        id = res['nzo_ids'][0]
        if not id:
            raise ApiError('failed to add nzb %s' % file)
        return id

    def list_nzbs(self, history=False):
        mode = 'history' if history else 'queue'
        res = self._send(mode=mode, start='START', limit='LIMIT')
        return res[mode].get('slots', [])

    def _get_nzb(self, id, history):
        for nzb in self.list_nzbs(history=history):
            if nzb['nzo_id'] == id:
                return nzb

    def get_nzb(self, id, history=False):
        res = self._get_nzb(id, history=history)
        if res:
            files = self._send(mode='get_files', value=id)
            if files.get('files'):
                res.update(files)
        return res

    def get_config(self):
        res = self._send(mode='get_config')
        return res.get('config', {})

    def remove_nzb(self, id, history=False):
        mode = 'history' if history else 'queue'
        self._send(mode=mode, name='delete', value=id)
        return True
