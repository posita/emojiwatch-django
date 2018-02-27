# -*- encoding: utf-8; test-case-name: tests.test_views -*-

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

import html
import json.decoder
import re
import slacker

import django.http as d_http
import django.utils.decorators as d_u_decorators
import django.views.decorators.csrf as d_v_d_csrf
import django.views.decorators.http as d_v_d_http
import django.views.generic as d_v_generic

from gettext import gettext

from . import (
    LOGGER,
    SLACK_VERIFICATION_TOKEN,
)
from .models import (
    SlackWorkspaceEmojiWatcher,
    TEAM_ID_MAX_LEN,
    TEAM_ID_RE,
)

# ---- Data --------------------------------------------------------------

__all__ = ()

_CHALLENGE_MAX_LEN = 1023
_EMOJI_NAME_MAX_LEN = 255
_EMOJI_URL_MAX_LEN = 1023
_EMOJIS_MAX_LEN = 32
_FIELD_MAX_LEN = 63
_SHRUG = str(u'\u00af\\_(\u30c4)_/\u00af')
_SUB_HANDLERS_BY_SUBTYPE = {}  # type: typing.Dict[typing.Text, typing.Callable[[SlackWorkspaceEmojiWatcher, typing.Dict], slacker.Response]]
_UNRECOGNIZED_JSON_BODY_ERR = 'unrecognized JSON structure from request body'

# ---- Exceptions --------------------------------------------------------

try:
    from json.decoder import JSONDecodeError  # type: ignore # py2
except ImportError:
    JSONDecodeError = ValueError  # type: ignore # py2

# ========================================================================
class RequestPayloadValidationError(Exception):

    # ---- Constructor ---------------------------------------------------

    def __init__(  # noqa:F811 # pylint: disable=keyword-arg-before-vararg
            self,
            message=gettext(_UNRECOGNIZED_JSON_BODY_ERR),
            response=d_http.HttpResponseBadRequest(),
            *args,
            **kw
    ):  # type: (typing.Text, d_http.HttpResponse, *typing.Any, **typing.Any) -> None
        super().__init__(*args, **kw)  # type: ignore # py2
        self._message = message
        self._response = response

    # ---- Properties ----------------------------------------------------

    @property
    def message(  # type: ignore # py2
            self,
    ):  # type: (...) -> typing.Text
        return self._message  # type: ignore

    @property
    def response(
            self,
    ):  # type: (...) -> d_http.Response
        return self._response  # type: ignore

# ---- Classes -----------------------------------------------------------

# ========================================================================
class CsrfExemptRedirectView(d_v_generic.RedirectView):

    @d_u_decorators.method_decorator(d_v_d_http.require_GET)
    @d_u_decorators.method_decorator(d_v_d_csrf.csrf_exempt)
    def dispatch(self, request, *args, **kw):
        return super(CsrfExemptRedirectView, self).dispatch(request, *args, **kw)

# ---- Functions ---------------------------------------------------------

# ========================================================================
@d_v_d_http.require_POST
@d_v_d_csrf.csrf_exempt
def event_hook_handler(
        request,  # type: d_http.HttpRequest
):  # type: (...) -> d_http.HttpResponse
    if not SLACK_VERIFICATION_TOKEN:
        LOGGER.critical("EMOJIWATCH['slack_verification_token'] setting is missing")

        return d_http.HttpResponseServerError()

    slack_retry_num = request.META.get('HTTP_X_SLACK_RETRY_NUM', 0)
    slack_retry_reason = request.META.get('HTTP_X_SLACK_RETRY_REASON', None)

    if slack_retry_num:
        LOGGER.info(gettext("Slack retry attempt %s ('%s')"), slack_retry_num, slack_retry_reason)

    content_type = request.META.get('HTTP_CONTENT_TYPE', 'application/json')

    if content_type != 'application/json' \
            or request.encoding not in {None, 'utf-8', 'UTF-8', 'csUTF8'}:
        return d_http.HttpResponse(status_code=415)

    try:
        payload_data = json.loads(request.body.decode('utf-8'))  # type: typing.Dict
    except (JSONDecodeError, UnicodeDecodeError):
        LOGGER.info(gettext('unable to parse JSON from request body'))
        truncate_len = 1024
        half_truncate_len = truncate_len >> 1

        if len(request.body) > truncate_len:
            LOGGER.debug('%r', request.body[:half_truncate_len] + b'<...>' + request.body[-half_truncate_len:])
        else:
            LOGGER.debug('%r', request.body)

        return d_http.HttpResponseBadRequest()

    try:
        try:
            verification_token = payload_data['token']
        except (KeyError, TypeError):
            verification_token = None
            LOGGER.info(gettext(_UNRECOGNIZED_JSON_BODY_ERR + " (missing 'token')"))  # pylint: disable=logging-not-lazy

        if not verification_token \
                or verification_token != SLACK_VERIFICATION_TOKEN:
            raise RequestPayloadValidationError(
                message=gettext('bad verification token'),
                response=d_http.HttpResponseForbidden(),
            )

        try:
            call_type = payload_data['type']
        except KeyError:
            raise RequestPayloadValidationError(
                message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + " (missing 'type')"),
            )

        if call_type == 'url_verification':
            try:
                challenge = payload_data['challenge']
            except KeyError:
                raise RequestPayloadValidationError(
                    message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + " (missing 'challenge')"),
                )

            if not isinstance(challenge, str) \
                    or len(challenge) > _CHALLENGE_MAX_LEN:
                raise RequestPayloadValidationError(
                    message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + ' (unrecognized challenge)'),
                )

            return d_http.HttpResponse(challenge, content_type='text/plain')

        if call_type != 'event_callback':
            raise RequestPayloadValidationError(
                message=gettext('unrecognized call type'),
            )

        try:
            event = payload_data.get('event', {})
            event_type = event['type']
            event_subtype = event['subtype']
            team_id = payload_data['team_id']
        except (AttributeError, KeyError, TypeError):
            raise RequestPayloadValidationError()

        if not isinstance(event_type, str) \
                or len(event_type) > _FIELD_MAX_LEN \
                or event_type != 'emoji_changed':
            raise RequestPayloadValidationError(
                message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + ' (unrecognized event type)'),
            )

        try:
            if not isinstance(event_subtype, str) \
                    or len(event_subtype) > _FIELD_MAX_LEN:
                raise ValueError

            subhandler = _SUB_HANDLERS_BY_SUBTYPE[event_subtype]
        except (KeyError, ValueError):
            raise RequestPayloadValidationError(
                message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + ' (unrecognized event subtype)'),
            )

        if not isinstance(team_id, str) \
                or len(team_id) > TEAM_ID_MAX_LEN \
                or not re.search(TEAM_ID_RE, team_id):
            raise RequestPayloadValidationError(
                message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + ' (unrecognized team_id)'),
            )

        team = SlackWorkspaceEmojiWatcher.objects.filter(team_id=team_id).first()

        if team is None:
            raise RequestPayloadValidationError(
                message=gettext('no such team ({})').format(team_id),
            )

        try:
            # By this point we're confident that event is a dict
            subhandler(team, event)
        except slacker.Error as exc:
            if exc.args == ('invalid_auth',):
                raise RequestPayloadValidationError(
                    message=gettext('call to Slack API failed auth'),
                    response=d_http.HttpResponseForbidden(),
                )

            # Log, but otherwise ignore errors from our callbacks to Slack's
            # API
            LOGGER.info(gettext('falled call to Slack'))
            LOGGER.debug(_SHRUG, exc_info=True)

    except RequestPayloadValidationError as exc:
        if exc.message:
            LOGGER.info(exc.message)

        LOGGER.debug('%r', payload_data)

        return exc.response

    return d_http.HttpResponse()

# ========================================================================
def _as_user(
        team,  # type: SlackWorkspaceEmojiWatcher
):  # type: (...) -> typing.Optional[bool]
    # as_user can only be non-None if it's a bot token (see
    # <https://api.slack.com/docs/token-types>)
    return False if re.search(r'\Axoxb-', team.access_token) else None

# ========================================================================
def _icon_emoji(
        team,  # type: SlackWorkspaceEmojiWatcher
):  # type: (...) -> typing.Optional[typing.Text]
    return team.icon_emoji if team.icon_emoji else None

# ========================================================================
def _handle_add(
        team,  # type: SlackWorkspaceEmojiWatcher
        event,  # type: typing.Dict
):  # type: (...) -> typing.Optional[slacker.Response]
    emoji_name = event.get('name', '')  # type: typing.Optional[typing.Text]
    emoji_url = event.get('value', '')  # type: typing.Optional[typing.Text]

    if not isinstance(emoji_name, str) \
            or not emoji_name \
            or len(emoji_name) > _EMOJI_NAME_MAX_LEN:
        raise RequestPayloadValidationError(
            message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + ' (unrecognized event name)'),
        )

    if not isinstance(emoji_url, str) \
            or len(emoji_url) > _EMOJI_URL_MAX_LEN:
        raise RequestPayloadValidationError(
            message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + ' (unrecognized event value)'),
        )

    if emoji_url:
        attachments = [  # needs to be a list, not a tuple
            {
                'fallback': '<{}>'.format(emoji_url),
                'image_url': emoji_url,
            },
        ]  # type: typing.Optional[typing.List[typing.Dict[typing.Text, typing.Text]]]
    else:
        attachments = None

    return slacker.Slacker(team.access_token).chat.post_message(
        team.channel_id,
        html.escape(gettext('added `:{}:`').format(emoji_name)),
        as_user=_as_user(team),
        attachments=attachments,
        icon_emoji=_icon_emoji(team),
    )

# ========================================================================
def _handle_remove(
        team,  # type: SlackWorkspaceEmojiWatcher
        event,  # type: typing.Dict
):  # type: (...) -> slacker.Response
    emoji_names = event.get('names', [])  # type: typing.Optional[typing.List[typing.Text]]

    if not isinstance(emoji_names, list):
        raise RequestPayloadValidationError(
            message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + ' (unrecognized event names)'),
        )

    if not emoji_names:
        return None

    too_many = len(emoji_names) > _EMOJIS_MAX_LEN
    emoji_names = emoji_names[:_EMOJIS_MAX_LEN]

    if any((not isinstance(emoji_name, str) for emoji_name in emoji_names[:_EMOJIS_MAX_LEN])) \
            or any((len(emoji_name) > _EMOJI_NAME_MAX_LEN for emoji_name in emoji_names)):
        raise RequestPayloadValidationError(
            message=gettext(_UNRECOGNIZED_JSON_BODY_ERR + ' (unrecognized event names)'),
        )

    return slacker.Slacker(team.access_token).chat.post_message(
        team.channel_id,
        html.escape(gettext('removed {}{}').format(', '.join('`:{}:`'.format(name) for name in emoji_names[:_EMOJIS_MAX_LEN]), '...' if too_many else '')),
        as_user=_as_user(team),
        icon_emoji=_icon_emoji(team),
    )

# ---- Initialization ----------------------------------------------------

_SUB_HANDLERS_BY_SUBTYPE.update((
    ('add', _handle_add),
    ('remove', _handle_remove),
))
