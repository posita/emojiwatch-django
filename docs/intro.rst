.. -*- encoding: utf-8 -*-
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    >>>>>>>>>>>>>>> IMPORTANT: READ THIS BEFORE EDITING! <<<<<<<<<<<<<<<
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    Please keep each sentence on its own unwrapped line.
    It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
    Thank you!

.. toctree::
   :maxdepth: 3
   :hidden:

Copyright and other protections apply.
Please see the accompanying :doc:`LICENSE <LICENSE>` and :doc:`CREDITS <CREDITS>` file(s) for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If those files are missing or appear to be modified from their originals, then please contact the author before viewing or using this software in any capacity.

Introduction
============

``django-emojiwatch`` is a bare bones Slack app for posting custom emoji updates to a designated channel.
It is implemented as a Django app.
It was loosely inspired by Khan Academy's |emojiwatch|_, which provides similar functionality, but for hosting on on Google App Engine.

.. |emojiwatch| replace:: ``emojiwatch``
.. _`emojiwatch`: https://github.com/Khan/emojiwatch

License
-------

``django-emojiwatch`` is licensed under the `MIT License <https://opensource.org/licenses/MIT>`_.
See the :doc:`LICENSE <LICENSE>` file for details.
Source code is `available on GitHub <https://github.com/posita/django-emojiwatch>`__.

Installation
------------

Django
~~~~~~

Installation can be performed via ``pip`` (which will download and install the `latest release <https://pypi.python.org/pypi/django-emojiwatch/>`__):

.. code-block:: console

   % pip install django-emojiwatch
   ...

Alternately, you can download the sources (e.g., `from GitHub <https://github.com/posita/django-emojiwatch>`__) and run ``setup.py``:

.. code-block:: console

   % git clone https://github.com/posita/django-emojiwatch
   ...
   % cd django-emojiwatch
   % python setup.py install
   ...

Now you can add it to your ``DJANGO_SETTINGS_MODULE``:

.. code-block:: python

    INSTALLED_APPS = (
        # ...
        'emojiwatch',
    )

    EMOJIWATCH = {
        'slack_verification_token': '...',
    }

And add it to your site-wide URLs:

.. code-block:: python

    from django.conf.urls import include, url

    urlpatterns = (
        # ...
        url(
            r'^emojiwatch/',  # or werever you want
            include('emojiwatch.urls'),
        ),
        # ...
    )

If you haven't already, you'll also need to `enable the admin site <https://docs.djangoproject.com/en/2.0/ref/contrib/admin/#overview>`__ for your Django installation.

Configuring Token Encryption in Django's Database
+++++++++++++++++++++++++++++++++++++++++++++++++

By default, workspace IDs will be encrypted using a hash of the ``SECRET_KEY`` Django setting.
To override this, use the ``FERNET_KEYS`` setting. For example:

.. code-block:: python

    from os import environ
    SECRET_KEY = environ['SECRET_KEY']
    # Use only Base64-encoded 32 byte values for keys; don't derive them
    # from arbitrary strings
    FERNET_USE_HKDF = False
    # For supporting any legacy keys that were used when FERNET_USE_HKDF
    # was True
    from fernet_fields.hkdf import derive_fernet_key
    # The keys
    FERNET_KEYS = [
        # The first entry is the current key (for encrypting and
        # decrypting)
        environ['FERNET_KEY'],
        # Optional additional entries are older keys for decrypting only
        # environ['OLD_FERNET_KEY_1'],
        # Equivalent to the default key
        # derive_fernet_key(SECRET_KEY),
    ]

See `the docs <http://django-fernet-fields.readthedocs.io/en/latest/#keys>`__ for details.

Slack App Setup
~~~~~~~~~~~~~~~

For illustration, we'll create a `workspace-based Slack app <https://api.slack.com/docs/token-types#workspace>`__, but we could just as easily use a traditional one.

TODO: Finish this section.

Requirements
------------

You'll a Slack account (and admin approval) for setting up your app.
A modern version of Python is required:

* `cPython <https://www.python.org/>`_ (2.7 or 3.4+)
* `PyPy <http://pypy.org/>`_ (Python 2.7 or 3.4+ compatible)

``django-emojiwatch`` has the following dependencies (which will be installed automatically):

* |Django|_ (1.8 or higher)
* |django-fernet-fields|_
* |future|_
* |slacker|_

.. |Django| replace:: ``Django``
.. _`Django`: https://www.djangoproject.com/
.. |django-fernet-fields| replace:: ``django-fernet-fields``
.. _`django-fernet-fields`: https://django-fernet-fields.readthedocs.io/
.. |future| replace:: ``future``
.. _`future`: http://python-future.org/
.. |slacker| replace:: ``slacker``
.. _`slacker`: https://github.com/os/slacker
