# Copyright (c) 2022, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
author:
    - Felix Fontein (@felixfontein)
name: dummy
short_description: Just print information
version_added: 0.0.1
description:
    - This just prints information on what is going on for a connection with pipelining enabled.
options:
    remote_user:
        type: str
        description:
            - The remote user.
        vars:
            - name: ansible_user
        ini:
            - section: defaults
              key: remote_user
        env:
            - name: ANSIBLE_REMOTE_USER
        cli:
            - name: user
        keyword:
            - name: remote_user
    remote_addr:
        type: str
        description:
            - The remote address.
        default: inventory_hostname
        vars:
            - name: inventory_hostname
            - name: ansible_host
'''

import io
import os
import os.path
import random
import shutil

from ansible.errors import AnsibleFileNotFound, AnsibleConnectionFailure
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display


display = Display()


def create_id():
    length = 8
    v = hex(random.randrange(0, 1 << (4 * length)))[2:]
    return '[%s%s]' % ('0' * (length - len(v)), v)


plugin_id = create_id()
display.v('[%s] Plugin loaded' % (plugin_id, ))


class Connection(ConnectionBase):
    '''Dummy connection'''

    transport = 'felixfontein.playground.dummy'
    has_pipelining = True

    def _log(self, msg, **kwargs):
        display.v('[%s:%s] %s' % (plugin_id, self._id, msg), **kwargs)

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)
        self._id = create_id()
        self._log('Initialized')

        if getattr(self._shell, "_IS_WINDOWS", False):
            self._log('This is a windows shell; adjusting accordingly')
            self.module_implementation_preferences = ('.ps1', '.exe', '')

    def _connect(self, port=None):
        super(Connection, self)._connect()
        self._log(
            'Connect (_connected=%s)' % self._connected,
            host=self.get_option('remote_addr'))
        if not self._connected:
            self._log(
                'Connecting: user = %r' % (self.get_option('remote_user'), ),
                host=self.get_option('remote_addr'))
            self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=False):
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        command = [self._play_context.executable, '-c', to_text(cmd)]

        do_become = self.become and self.become.expect_prompt() and sudoable
        need_stdin = True if (in_data is not None) or do_become else False

        self._log(
            'Executing command: user = %r, command = %r, do_become = %s, need_stdin = %s' % (
                self.get_option('remote_user'), command, do_become, need_stdin),
            host=self.get_option('remote_addr'))

        # We handle Python detection manually so that it won't error out:
        if any('echo PLATFORM; uname; echo FOUND' in cmd for cmd in command):
            self._log(
                'This command is (probably) the Python interpreter discovery; returning canned response',
                host=self.get_option('remote_addr'))
            return 0, b'PLATFORM\nFOUND\n/foo/python\nENDFOUND', b''

        return 0, b'{}', b''

    def _prefix_login_path(self, remote_path):
        if getattr(self._shell, "_IS_WINDOWS", False):
            import ntpath
            return ntpath.normpath(remote_path)
        else:
            if not remote_path.startswith(os.path.sep):
                remote_path = os.path.join(os.path.sep, remote_path)
            return os.path.normpath(remote_path)

    def put_file(self, in_path, out_path):
        super(Connection, self).put_file(in_path, out_path)

        new_out_path = self._prefix_login_path(out_path)

        self._log(
            'Putting file: user = %r, in_path = %r, out_path = %r, new_out_path = %r' % (
                self.get_option('remote_user'), in_path, out_path, new_out_path),
            host=self.get_option('remote_addr'))

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)

        new_in_path = self._prefix_login_path(in_path)

        self._log(
            'Fetching file: user = %r, in_path = %r, out_path = %r, new_in_path = %r' % (
                self.get_option('remote_user'), in_path, out_path, new_in_path),
            host=self.get_option('remote_addr'))

    def close(self):
        super(Connection, self).close()
        self._log(
            'Closing connection: user = %r' % (self.get_option('remote_user'), ),
            host=self.get_option('remote_addr'))
        self._connected = False
