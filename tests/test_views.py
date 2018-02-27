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

import json
import slacker
import unittest

try:
    import django.urls as d_urls
except ImportError:
    import django.core.urlresolvers as d_urls

import django.http as d_http
import django.test as d_test

if __name__ == '__main__':
    import tests
    tests.setup()

from emojiwatch import SLACK_VERIFICATION_TOKEN
from emojiwatch.models import (
    SlackWorkspaceEmojiWatcher,
    TEAM_ID_MAX_LEN,
)
from emojiwatch.views import (
    RequestPayloadValidationError,
    _CHALLENGE_MAX_LEN,
    _FIELD_MAX_LEN,
)

from tests.symmetries import mock


# ---- Data --------------------------------------------------------------

__all__ = ()

# ---- Classes -----------------------------------------------------------

# ========================================================================
class RequestPayloadValidationErrorTestCase(unittest.TestCase):

    # ---- Methods -------------------------------------------------------

    def test_constructors(self):
        # type: (...) -> None
        message = 'Hey!'
        response = d_http.HttpResponseServerError()

        exc = RequestPayloadValidationError()
        self.assertEqual(exc.message, 'unrecognized JSON structure from request body')
        self.assertIsInstance(exc.response, d_http.HttpResponseBadRequest)

        exc = RequestPayloadValidationError(message)
        self.assertEqual(exc.message, message)
        self.assertIsInstance(exc.response, d_http.HttpResponseBadRequest)

        exc = RequestPayloadValidationError(message=message)
        self.assertEqual(exc.message, message)
        self.assertIsInstance(exc.response, d_http.HttpResponseBadRequest)

        exc = RequestPayloadValidationError(response=response)
        self.assertEqual(exc.message, 'unrecognized JSON structure from request body')
        self.assertEqual(exc.response, response)

        exc = RequestPayloadValidationError(message, response)
        self.assertEqual(exc.message, message)
        self.assertEqual(exc.response, response)

        exc = RequestPayloadValidationError(message, response=response)
        self.assertEqual(exc.message, message)
        self.assertEqual(exc.response, response)

        exc = RequestPayloadValidationError(message=message, response=response)
        self.assertEqual(exc.message, message)
        self.assertEqual(exc.response, response)

        # TODO: These should all generate MyPy errors
        RequestPayloadValidationError('', True)
        RequestPayloadValidationError('', response=True)
        RequestPayloadValidationError(message='', response=True)

# ========================================================================
class EventHandlerTestCaseBase(d_test.TestCase):

    # ---- Data ----------------------------------------------------------

    WORKSPACE = {
        'team_id': 'T123ABC',
        'access_token': 'xoxa-1f2e3d-4c5b6a',
        'channel_id': 'C123ABC',
        'icon_emoji': ':blush:',
    }

    BOT = {
        'team_id': 'T456DEF',
        'access_token': 'xoxb-4c5b6a-1f2e3d',
        'channel_id': 'C456DEF',
        'icon_emoji': ':smirk:',
    }

    # ---- Properties ----------------------------------------------------

    @property
    def good_add_event(self):
        # type: (...) -> typing.Dict
        return {
            'event': {
                'name': 'blam',
                'subtype': 'add',
                'type': 'emoji_changed',
                'value': 'https://gulfcoastmakers.files.wordpress.com/2015/03/blam.jpg',
            },

            'team_id': self.WORKSPACE['team_id'],
            'token': SLACK_VERIFICATION_TOKEN,
            'type': 'event_callback',
        }

    @property
    def good_remove_event(self):
        # type: (...) -> typing.Dict
        return {
            'event': {
                'names': [
                    'biff',
                    'blam',
                    'pow',
                    'zok',
                ],
                'subtype': 'remove',
                'type': 'emoji_changed',
            },

            'team_id': self.WORKSPACE['team_id'],
            'token': SLACK_VERIFICATION_TOKEN,
            'type': 'event_callback',
        }

    @property
    def good_url_verification(self):
        # type: (...) -> typing.Dict
        return {
            'challenge': '',
            'token': SLACK_VERIFICATION_TOKEN,
            'type': 'url_verification',
        }

    # ---- Hooks ---------------------------------------------------------

    def setUp(self):
        super().setUp()  # type: ignore # py2
        SlackWorkspaceEmojiWatcher(**self.WORKSPACE).save()
        SlackWorkspaceEmojiWatcher(**self.BOT).save()

    # ---- Methods -------------------------------------------------------

    def post_event_hook(self, payload_data, content_type=None, encoding=None):
        if not isinstance(payload_data, str):
            # See <https://tools.ietf.org/html/rfc8259#section-8.1> and
            # <https://tools.ietf.org/html/rfc8259#section-11> (JSON is
            # UTF-8 and charset parameter should be omitted). In addition,
            # at least with Django dev, if an explicit charset is
            # provided, data is blindly assumed to be a Unicode string
            # (not raw bytes) and the charset will be used to encode it.
            content_type = 'application/json'
            encoding = None
            payload_data = json.dumps(payload_data)

        return self.client.post(
            d_urls.reverse('emojiwatch:event_hook'),
            content_type='{}{}{}'.format(content_type, '; charset=' if encoding else '', encoding),
            data=payload_data,
            follow=True,
        )

# ========================================================================
class EventHandlerTestCase(EventHandlerTestCaseBase):

    # ---- Methods -------------------------------------------------------

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_bad_event(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            for event in (
                    None,
                    '<...>',
                    [],
                    '**' * _FIELD_MAX_LEN,
            ):
                payload_data['event'] = event
                res = self.post_event_hook(payload_data)
                self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_bad_event_type(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            for event_type in (
                    None,
                    '<...>',
                    [],
                    {'type': None},
                    '**' * _FIELD_MAX_LEN,
            ):
                payload_data['event']['type'] = event_type
                res = self.post_event_hook(payload_data)
                self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_bad_event_subtype(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            for event_type in (
                    None,
                    '<...>',
                    [],
                    {'subtype': None},
                    '**' * _FIELD_MAX_LEN,
            ):
                payload_data['event']['subtype'] = event_type
                res = self.post_event_hook(payload_data)
                self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_bad_team(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            for team_id in (
                    None,
                    '<...>',
                    'T' + 'A' * TEAM_ID_MAX_LEN,
                    list(self.WORKSPACE['team_id']),
                    {self.WORKSPACE['team_id']: None},
            ):
                payload_data['team_id'] = team_id
                res = self.post_event_hook(payload_data)
                self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_bad_type(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            for event_type in (
                    None,
                    '<...>',
                    list('emoji_changed'),
                    {'emoji_changed': None},
                    '**' * _FIELD_MAX_LEN,
            ):
                payload_data['event']['type'] = event_type
                res = self.post_event_hook(payload_data)
                self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_no_event(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            del payload_data['event']
            res = self.post_event_hook(payload_data)
            self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_no_event_type(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            del payload_data['event']['type']
            res = self.post_event_hook(payload_data)
            self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_no_event_subtype(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            del payload_data['event']['subtype']
            res = self.post_event_hook(payload_data)
            self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_no_team(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            del payload_data['team_id']
            res = self.post_event_hook(payload_data)
            self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_emoji_no_type(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
        ):
            del payload_data['event']['type']
            res = self.post_event_hook(payload_data)
            self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_payload_bad_json(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')
        res = self.post_event_hook(str('---'), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_payload_bad_type(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
                self.good_url_verification,
        ):
            for payload_type in (
                    None,
                    '<...>',
                    list('event_callback'),
                    {'event_callback': None},
                    '**' * _FIELD_MAX_LEN,
            ):
                payload_data['type'] = payload_type
                res = self.post_event_hook(payload_data)
                self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_payload_no_type(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
                self.good_url_verification,
        ):
            del payload_data['type']
            res = self.post_event_hook(payload_data)
            self.assertEqual(res.status_code, 400)

# ========================================================================
class EmojiAddTestCase(EventHandlerTestCaseBase):

    # ---- Methods -------------------------------------------------------

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_add_emoji(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        good_add_event = self.good_add_event
        res = self._post_add_event(self.WORKSPACE, good_add_event, mocked_post_message)
        self.assertEqual(res.status_code, 200)

        good_add_event['team_id'] = self.BOT['team_id']
        res = self._post_add_event(self.BOT, good_add_event, mocked_post_message, as_user=False)
        self.assertEqual(res.status_code, 200)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_add_emoji_invalid_auth(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = slacker.Error('invalid_auth')
        res = self._post_add_event(self.WORKSPACE, self.good_add_event, mocked_post_message)
        self.assertEqual(res.status_code, 403)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_add_emoji_slacker_errors_ignored(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = slacker.Error()
        res = self._post_add_event(self.WORKSPACE, self.good_add_event, mocked_post_message)
        self.assertEqual(res.status_code, 200)

    def _post_add_event(
            self,
            team_dict,  # type: typing.Dict
            add_event,  # type: typing.Dict
            mocked_post_message,  # type: mock.MagicMock
            as_user=None,  # type: typing.Optional[bool]
    ):
        # type: (...) -> d_http.Response
        add_event.setdefault('team_id', team_dict['team_id'])
        emoji_name = add_event['event']['name']
        emoji_url = add_event['event']['value']
        res = self.post_event_hook(add_event)
        mocked_post_message.assert_called_with(
            team_dict['channel_id'],
            'added `:{}:`'.format(emoji_name),
            attachments=[{
                'fallback': '<{}>'.format(emoji_url),
                'image_url': emoji_url,
            }],
            as_user=as_user,
            icon_emoji=team_dict['icon_emoji'],
        )

        return res

# ========================================================================
class EmojiRemoveTestCase(EventHandlerTestCaseBase):

    # ---- Methods -------------------------------------------------------

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_remove_emoji(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        good_remove_event = self.good_remove_event
        res = self._post_remove_event(self.WORKSPACE, good_remove_event, mocked_post_message)
        self.assertEqual(res.status_code, 200)

        good_remove_event['team_id'] = self.BOT['team_id']
        res = self._post_remove_event(self.BOT, good_remove_event, mocked_post_message, as_user=False)
        self.assertEqual(res.status_code, 200)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_remove_emoji_invalid_auth(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = slacker.Error('invalid_auth')
        res = self._post_remove_event(self.WORKSPACE, self.good_remove_event, mocked_post_message)
        self.assertEqual(res.status_code, 403)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_event_remove_emoji_slacker_errors_ignored(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = slacker.Error()
        res = self._post_remove_event(self.WORKSPACE, self.good_remove_event, mocked_post_message)
        self.assertEqual(res.status_code, 200)

    def _post_remove_event(
            self,
            team_dict,  # type: typing.Dict
            remove_event,  # type: typing.Dict
            mocked_post_message,  # type: mock.MagicMock
            as_user=None,  # type: typing.Optional[bool]
    ):
        # type: (...) -> d_http.Response
        remove_event.setdefault('team_id', team_dict['team_id'])
        emoji_names = remove_event['event']['names']
        res = self.post_event_hook(remove_event)
        mocked_post_message.assert_called_with(
            team_dict['channel_id'],
            'removed `:{}:`'.format(':`, `:'.join(emoji_names)),
            as_user=as_user,
            icon_emoji=team_dict['icon_emoji'],
        )

        return res

# ========================================================================
class VerificationTestCase(EventHandlerTestCaseBase):

    # ---- Methods -------------------------------------------------------

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_bad_challenge(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')
        payload_data = self.good_url_verification

        for challenge in (
                None,
                list('<...>'),
                {'challenge': None},
                '**' * _CHALLENGE_MAX_LEN,
        ):
            payload_data['challenge'] = challenge
            res = self.post_event_hook(payload_data)
            self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_bad_token(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')

        res = self.post_event_hook({
            'token': '<...>',
        })

        self.assertEqual(res.status_code, 403)

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
                self.good_url_verification,
        ):
            for token in (
                    None,
                    '<...>',
                    list(SLACK_VERIFICATION_TOKEN),
                    {'token': None},
                    '**' * _FIELD_MAX_LEN,
            ):
                payload_data['token'] = token
                res = self.post_event_hook(payload_data)
                self.assertEqual(res.status_code, 403)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_no_challenge(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')
        payload_data = self.good_url_verification
        del payload_data['challenge']
        res = self.post_event_hook(payload_data)
        self.assertEqual(res.status_code, 400)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_no_token(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')
        res = self.post_event_hook({})
        self.assertEqual(res.status_code, 403)

        for payload_data in (
                self.good_add_event,
                self.good_remove_event,
                self.good_url_verification,
        ):
            del payload_data['token']
            res = self.post_event_hook(payload_data)
            self.assertEqual(res.status_code, 403)

    @mock.patch.object(slacker.Chat, 'post_message')
    def test_url_verification(
            self,
            mocked_post_message,  # type: mock.MagicMock
    ):
        # type: (...) -> None
        mocked_post_message.side_effect = AssertionError('should not have reached slacker.Chat.post_message')
        payload_data = self.good_url_verification
        payload_data['challenge'] = 'NXEJp99-JO7kCaVrBbMteU4EhOzW3Bek59_NXmR6uXo='
        res = self.post_event_hook(payload_data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(payload_data['challenge'], res.content.decode('utf-8'))

# ---- Initialization ----------------------------------------------------

if __name__ == '__main__':
    tests.main()
