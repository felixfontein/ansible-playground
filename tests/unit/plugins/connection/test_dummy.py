# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2022, Felix Fontein

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from io import StringIO

from ansible_collections.community.internal_test_tools.tests.unit.compat import unittest

from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader


class TestDummyConnectionClass(unittest.TestCase):

    def setUp(self):
        self.play_context = PlayContext()
        self.play_context.prompt = (
            '[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: '
        )
        self.in_stream = StringIO()
        self.connection = connection_loader.get('felixfontein.playground.dummy', self.play_context, self.in_stream)

    def tearDown(self):
        pass

    def test_foo(self):
        pass  # TODO
