# -*- encoding: utf-8 -*-
# ======================================================================
"""
Copyright and other protections apply. Please see the accompanying
:doc:`LICENSE <LICENSE>` and :doc:`CREDITS <CREDITS>` file(s) for rights
and restrictions governing use of this software. All rights not
expressly waived or licensed are reserved. If those files are missing or
appear to be modified from their originals, then please contact the
author before viewing or using this software in any capacity.
"""
# ======================================================================

from __future__ import absolute_import, division, print_function

TYPE_CHECKING = False  # from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

from builtins import *  # noqa: F401,F403 # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import *  # noqa: F401,F403 # pylint: disable=no-name-in-module,redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

# ---- Imports ---------------------------------------------------------

import django.conf.urls as d_c_urls

from .version import (
    __release__,
    __version__,
)

from .views import (
    CsrfExemptRedirectView,
    event_hook_handler,
)

# ---- Data ------------------------------------------------------------

__all__ = ()

_RTD_RELEASE = __release__ if __version__ != (0, 0, 0) else 'latest'
_RTD_URL = 'https://django-emojiwatch.readthedocs.io/en/{}/'.format(_RTD_RELEASE)

app_name = 'emojiwatch'

urlpatterns = (
    d_c_urls.url(r'^event_hook$', event_hook_handler, name='event_hook'),
    d_c_urls.url(r'^$', CsrfExemptRedirectView.as_view(
        permanent=False,
        url=_RTD_URL,
    )),
)
