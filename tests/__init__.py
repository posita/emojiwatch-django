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

import os
import six
import unittest

# ---- Data --------------------------------------------------------------

__all__ = ()

# ---- Functions ---------------------------------------------------------

# ========================================================================
def setup():
    # Prerequisite to importing any Django models
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.django_settings')
    import django
    django.setup()

# ========================================================================
def main():  # type: (...) -> None
    import django.test.utils as d_t_utils

    try:
        d_t_utils.setup_test_environment()
        old_config = d_t_utils.setup_databases(verbosity=1, interactive=False)
        unittest.main()
    finally:
        d_t_utils.teardown_databases(old_config, verbosity=1)
        d_t_utils.teardown_test_environment()

# ---- Initialization ----------------------------------------------------

# See <https://github.com/python/typeshed/issues/1874>
unittest.TestCase.longMessage = True  # type: ignore # py2

# Python 3 complains that the assert*Regexp* methods are deprecated in
# favor of the analogous assert*Regex methods, which Python 2's unittest
# doesn't have; this monkey patch fixes all that nonsense
if not hasattr(unittest.TestCase, 'assertCountEqual'):
    setattr(unittest.TestCase, 'assertCountEqual', six.assertCountEqual)

if not hasattr(unittest.TestCase, 'assertRaisesRegex'):
    setattr(unittest.TestCase, 'assertRaisesRegex', six.assertRaisesRegex)

if not hasattr(unittest.TestCase, 'assertRegex'):
    setattr(unittest.TestCase, 'assertRegex', six.assertRegex)
