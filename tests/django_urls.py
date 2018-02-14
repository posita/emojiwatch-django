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

import django.conf.urls as d_c_urls
import django.contrib.admin as d_c_admin

# ---- Data --------------------------------------------------------------

__all__ = ()

try:
    # For Django 1.8
    emojiwatch_include = d_c_urls.include('emojiwatch.urls', app_name='emojiwatch', namespace='emojiwatch')  # pylint: disable=unexpected-keyword-arg,useless-suppression
except TypeError:
    # In Django 1.9+, app_name moved into the module (e.g., emojiwatch.urls.app_name)
    emojiwatch_include = d_c_urls.include('emojiwatch.urls', namespace='emojiwatch')

urlpatterns = (
    d_c_urls.url(r'^emojiwatch/', emojiwatch_include),
    d_c_urls.url(r'^admin/', d_c_admin.site.urls),
)
