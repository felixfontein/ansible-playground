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

import os
import os.path
import random
import sys
import threading

from ansible.module_utils.common.text.converters import to_text
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display


display = Display()


EMPHASIZE = '\033[1m'
FAINT = '\033[2m'
NORMAL = '\033[0m'


INTERNAL_COUNTER = 0
INTERNAL_COUNTER_LOCK = threading.Lock()


def get_color(no):
    return '\033[%s;%sm' % (30 + no % 8, 40 + (no + 1) % 8)


def _create_id(length, value):
    v = hex(value)[2:]
    return '%s%s%s%s' % (get_color(value), '0' * (length - len(v)), v, NORMAL)


def create_id():
    pid = os.getpid()
    try:
        thread_id = threading.get_native_id()
    except AttributeError:
        try:
            # Since this is generally something large, we cut it down to at most 16 bits
            thread_id = threading.get_ident() % 65536
        except AttributeError:
            # In Python 2.6 and 2.7, we need to cal current_thread().ident instead
            thread_id = threading.current_thread().ident % 65536
    return '%s/P:%s%s%s/T:%s%s%s' % (
        _create_id(8, random.randrange(0, 1 << 32)),
        get_color(pid), hex(pid)[2:], NORMAL,
        get_color(thread_id), hex(thread_id)[2:], NORMAL,
    )


def create_local_id():
    global INTERNAL_COUNTER

    with INTERNAL_COUNTER_LOCK:
        value = INTERNAL_COUNTER
        INTERNAL_COUNTER += 1

    return _create_id(2, value % 256)


def show_message(msg):
    display.display(msg)


plugin_id = create_id()
if all(name not in sys.argv[0] for name in ('importer', 'ansible-doc')):
    show_message('[%s] Plugin loaded' % (plugin_id, ))


class Connection(ConnectionBase):
    '''Dummy connection'''

    transport = 'felixfontein.playground.dummy'
    has_pipelining = True

    def _log(self, msg, **kwargs):
        if 'host' in kwargs:
            msg = '<%s%s%s> %s' % (EMPHASIZE, kwargs.pop('host'), NORMAL, msg)
        show_message('[%s/C:%s] %s' % (plugin_id, self._id, msg), **kwargs)

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)
        self._id = create_local_id()
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
                'Connecting: user = %s%r%s' % (FAINT, self.get_option('remote_user'), NORMAL),
                host=self.get_option('remote_addr'))
            self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=False):
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        command = [self._play_context.executable, '-c', to_text(cmd)]

        do_become = self.become and self.become.expect_prompt() and sudoable
        need_stdin = True if (in_data is not None) or do_become else False

        self._log(
            'Executing command: user = %s%r%s, command = %s%r%s, do_become = %s%s%s, need_stdin = %s%s%s' % (
                FAINT, self.get_option('remote_user'), NORMAL,
                FAINT, command, NORMAL,
                FAINT, do_become, NORMAL,
                FAINT, need_stdin, NORMAL),
            host=self.get_option('remote_addr'))

        # We handle Python detection manually so that it won't error out:
        if any('echo PLATFORM; uname; echo FOUND' in cmd for cmd in command):
            self._log(
                'This command is (probably) the Python interpreter discovery; returning canned response',
                host=self.get_option('remote_addr'))
            return 0, b'PLATFORM\nImaginary OS\nFOUND\n/foo/python\nENDFOUND', b''

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
            'Putting file: user = %s%r%s, in_path = %s%r%s, out_path = %s%r%s, new_out_path = %s%r%s' % (
                FAINT, self.get_option('remote_user'), NORMAL,
                FAINT, in_path, NORMAL,
                FAINT, out_path, NORMAL,
                FAINT, new_out_path, NORMAL),
            host=self.get_option('remote_addr'))

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)

        new_in_path = self._prefix_login_path(in_path)

        self._log(
            'Fetching file: user = %s%r%s, in_path = %s%r%s, out_path = %s%r%s, new_in_path = %s%r%s' % (
                FAINT, self.get_option('remote_user'), NORMAL,
                FAINT, in_path, NORMAL,
                FAINT, out_path, NORMAL,
                FAINT, new_in_path, NORMAL),
            host=self.get_option('remote_addr'))

    def close(self):
        super(Connection, self).close()
        self._log(
            'Closing connection: user = %s%r%s' % (FAINT, self.get_option('remote_user'), NORMAL),
            host=self.get_option('remote_addr'))
        self._connected = False
