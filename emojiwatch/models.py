# -*- encoding: utf-8; test-case-name: tests.test_models -*-

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

import fernet_fields
import slacker

from gettext import gettext

import django.core.validators as d_c_validators
import django.db.models as d_d_models

# ---- Data --------------------------------------------------------------

__all__ = ()

CHANNEL_ID_MAX_LEN = 63
CHANNEL_ID_RE = r'^C[0-9A-Z]*$'
TEAM_ID_MAX_LEN = 63
TEAM_ID_RE = r'^T[0-9A-Z]*$'
WORKSPACE_TOKEN_MAX_LEN = 255
WORKSPACE_TOKEN_RE = r'^xoxa-([0-9A-Fa-f]+)+'

# ---- Exceptions --------------------------------------------------------

# ========================================================================
class StaleVersionError(Exception): pass

# ---- Classes -----------------------------------------------------------

# ========================================================================
class VersionedModel(d_d_models.Model):
    """
    Class to stores the data associated with a particular team.
    """

    # ---- Inner classes -------------------------------------------------

    class Meta(object):
        abstract = True

    # ---- Properties ----------------------------------------------------

    _version = d_d_models.IntegerField(
        default=-0x80000000,
        null=False,
    )

    # ---- Overrides -----------------------------------------------------

    def save(self, *args, **kw):  # pylint: disable=arguments-differ
        # type: (...) -> None
        old_version = self._version

        if old_version < 0:
            self._version = 0
            kw['force_insert'] = True
            kw['force_update'] = False
        else:
            self._version += 1
            kw['force_insert'] = False
            kw['force_update'] = True

        try:
            super().save(*args, **kw)  # type: ignore # py2
        except:  # noqa: E722
            self._version = old_version
            raise

    def _do_update(self, base_qs, using, pk_val, values, update_fields, forced_update):  # pylint: disable=unused-argument
        # type: (...) -> bool
        # See
        # <https://github.com/django/django/blob/1.8/django/db/models/base.py#L827-L853>
        filtered = base_qs.filter(pk=pk_val, _version=self._version - 1)
        updated = filtered._update(values)  # pylint: disable=protected-access

        if updated == 0:
            raise StaleVersionError('{!r}._version {} is stale'.format(self, self._version - 1))

        assert updated == 1

        return True

# ========================================================================
class SlackWorkspaceEmojiWatcher(VersionedModel):
    """
    Class to stores the data associated with a particular team.
    """

    # ---- Inner classes -------------------------------------------------

    class Meta(object):
        verbose_name = 'Slack Workspace Emoji Watcher'

    # ---- Properties ----------------------------------------------------

    team_id = d_d_models.CharField(
        max_length=TEAM_ID_MAX_LEN,
        null=False,
        unique=True,
        validators=[
            d_c_validators.RegexValidator(TEAM_ID_RE, message=gettext('Must be of the format (e.g.) T123ABC...')),
        ],
        verbose_name=gettext('Team ID'),
    )

    team_id.short_description = gettext('Team ID (e.g., T123ABC...)')

    workspace_token = fernet_fields.EncryptedCharField(
        max_length=WORKSPACE_TOKEN_MAX_LEN,
        null=False,
        validators=[
            d_c_validators.RegexValidator(WORKSPACE_TOKEN_RE, message=gettext('Must be of the format (e.g.) xoxa-1f2e3d-4c5b6a...')),
        ],
        verbose_name=gettext('Workspace Token'),
    )

    channel_id = d_d_models.CharField(
        max_length=CHANNEL_ID_MAX_LEN,
        null=False,
        validators=[
            d_c_validators.RegexValidator(CHANNEL_ID_RE, message=gettext('Must be of the format (e.g.) C123ABC...')),
        ],
        verbose_name=gettext('Channel ID'),
    )

    @property
    def slack(self):
        return slacker.Slacker(self.workspace_token)
