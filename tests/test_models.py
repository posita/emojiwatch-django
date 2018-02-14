#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# ========================================================================
"""
Copyright and other protections apply. Please see the accompanying
:doc:`LICENSE <LICENSE>` and :doc:`CREDITS <CREDITS>` file(s) for rights
and restrictions governing use of this software. All rights not expressly
waived or licensed are reserved. If those files are missing or appear to
be modified from their originals, then please contact the author before
viewing or using this software in any capacity.
"""
# ========================================================================

from __future__ import absolute_import, division, print_function

TYPE_CHECKING = False  # from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

from builtins import *  # noqa: F401,F403 # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import *  # noqa: F401,F403 # pylint: disable=no-name-in-module,redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

# ---- Imports -----------------------------------------------------------

import re

import django.core.exceptions as d_c_exceptions
import django.db.utils as d_d_utils
import django.test as d_test

if __name__ == '__main__':
    import tests
    tests.setup()

from emojiwatch.models import (
    SlackWorkspaceEmojiWatcher,
    StaleVersionError,
)

# ---- Data --------------------------------------------------------------

__all__ = ()

# ---- Classes -----------------------------------------------------------

# ========================================================================
class SlackWorkspaceEmojiWatcherTestCase(d_test.TestCase):

    # ---- Methods -------------------------------------------------------

    def test_form_validation(self):
        self.assertEqual(len(SlackWorkspaceEmojiWatcher.objects.all()), 0)
        ws_emoji_watcher = SlackWorkspaceEmojiWatcher()

        with self.assertRaises(d_c_exceptions.ValidationError) as cm:
            ws_emoji_watcher.full_clean()

        for field in (
                'team_id',
                'workspace_token',
                'channel_id',
        ):
            self.assertEqual(cm.exception.message_dict[field][0], 'This field cannot be blank.', msg='(field = {!r})'.format(field))

        ws_emoji_watcher.team_id = '...'
        ws_emoji_watcher.workspace_token = '...'
        ws_emoji_watcher.channel_id = '...'

        with self.assertRaises(d_c_exceptions.ValidationError) as cm:
            ws_emoji_watcher.full_clean()

        for field, field_fmt in (
                ('team_id', 'T123ABC'),
                ('workspace_token', 'xoxa-1f2e3d-4c5b6a'),
                ('channel_id', 'C123ABC'),
        ):
            field_fmt_re = r'\AMust be of the format \(e\.g\.\) {}\.\.\.\Z'.format(re.escape(field_fmt))
            self.assertRegex(cm.exception.message_dict[field][0], field_fmt_re, msg='(field = {!r})'.format(field))

    def test_create(self):
        ws_emoji_watcher1 = SlackWorkspaceEmojiWatcher()
        ws_emoji_watcher1.team_id = 'T123ABC'
        ws_emoji_watcher1.workspace_token = 'xoxa-1f2e3d-4c5b6a'
        ws_emoji_watcher1.channel_id = 'C123ABC'
        self.assertLess(ws_emoji_watcher1._version, 0)  # pylint: disable=protected-access

        ws_emoji_watcher1.full_clean()
        ws_emoji_watcher1.save()
        self.assertEqual(len(SlackWorkspaceEmojiWatcher.objects.all()), 1)
        self.assertEqual(ws_emoji_watcher1._version, 0)  # pylint: disable=protected-access

        ws_emoji_watcher1.save()
        self.assertEqual(ws_emoji_watcher1._version, 1)  # pylint: disable=protected-access

        ws_emoji_watcher2 = SlackWorkspaceEmojiWatcher()
        ws_emoji_watcher2.team_id = 'T456DEF'
        ws_emoji_watcher2.workspace_token = 'xoxa-4c5b6a-1f2e3d'
        ws_emoji_watcher2.channel_id = 'C456DEF'
        self.assertLess(ws_emoji_watcher2._version, 0)  # pylint: disable=protected-access

        ws_emoji_watcher2.full_clean()
        ws_emoji_watcher2.save()
        self.assertEqual(len(SlackWorkspaceEmojiWatcher.objects.all()), 2)
        self.assertEqual(ws_emoji_watcher2._version, 0)  # pylint: disable=protected-access

        ws_emoji_watcher2.save()
        self.assertEqual(ws_emoji_watcher2._version, 1)  # pylint: disable=protected-access

    def test_team_id_uniqueness(self):
        ws_emoji_watcher1 = SlackWorkspaceEmojiWatcher()
        ws_emoji_watcher1.team_id = 'T123ABC'
        ws_emoji_watcher1.workspace_token = 'xoxa-1f2e3d-4c5b6a'
        ws_emoji_watcher1.channel_id = 'C123ABC'
        ws_emoji_watcher1.save()

        ws_emoji_watcher2 = SlackWorkspaceEmojiWatcher()
        ws_emoji_watcher2.team_id = ws_emoji_watcher1.team_id
        ws_emoji_watcher2.workspace_token = 'xoxa-4c5b6a-1f2e3d'
        ws_emoji_watcher2.channel_id = 'C456DEF'
        self.assertLess(ws_emoji_watcher2._version, 0)  # pylint: disable=protected-access
        old_version = ws_emoji_watcher2._version  # pylint: disable=protected-access

        with self.assertRaises(d_d_utils.IntegrityError):
            ws_emoji_watcher2.save()

        self.assertEqual(ws_emoji_watcher2._version, old_version)  # pylint: disable=protected-access

    def test_version_staleness(self):
        ws_emoji_watcher1 = SlackWorkspaceEmojiWatcher()
        ws_emoji_watcher1.team_id = 'T123ABC'
        ws_emoji_watcher1.workspace_token = 'xoxa-1f2e3d-4c5b6a'
        ws_emoji_watcher1.channel_id = 'C123ABC'
        ws_emoji_watcher1.save()

        ws_emoji_watcher2 = SlackWorkspaceEmojiWatcher.objects.filter(team_id=ws_emoji_watcher1.team_id).first()
        self.assertEqual(ws_emoji_watcher1, ws_emoji_watcher2)

        ws_emoji_watcher1.save()
        self.assertEqual(ws_emoji_watcher1, ws_emoji_watcher2)  # weird, but correct
        self.assertNotEqual(ws_emoji_watcher1._version, ws_emoji_watcher2._version)  # pylint: disable=protected-access

        old_version = ws_emoji_watcher2._version  # pylint: disable=protected-access

        with self.assertRaises(StaleVersionError):
            ws_emoji_watcher2.save()

        self.assertEqual(ws_emoji_watcher2._version, old_version)  # pylint: disable=protected-access

# ---- Initialization ----------------------------------------------------

if __name__ == '__main__':
    tests.main()
