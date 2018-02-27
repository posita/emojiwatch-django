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

Auth tokens and notes associated with a watcher are encrypted in the Django database using |django-fernet-fields|_.
By default, the encryption key is derived from the ``SECRET_KEY`` Django setting.
To override this, use the ``FERNET_KEYS`` and ``FERNET_USE_HKDF`` settings.
See `the docs <http://django-fernet-fields.readthedocs.io/en/latest/#keys>`__ for details.

Slack App and Watcher Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create a `new Slack app <https://api.slack.com/apps?new_app_token=1>`__ or a `legacy Slack app <https://api.slack.com/apps?new_app=1>`__.

#. Once created, navigate to the ``Basic Information`` settings section and copy the ``Verification Token`` (e.g., ``NS3PYxg1QR1l7s2G0fRDZ8uK``):

   .. image:: img/slack_app_verification_token.png
      :alt: Slack app verification Token

   This is what you'll use as the ``EMOJIWATCH['slack_verification_token']`` Django setting.

#. Add the ``emoji:read`` and ``chat:write`` (or ``chat:write:bot`` for legacy Slack apps) scopes to your app:

   .. image:: img/slack_app_oauth_scopes.png
      :alt: Slack app OAuth scopes

#. Navigate to the ``OAuth & Permission`` features section.
   If necessary, click ``Install App to Workspace``:

   .. image:: img/slack_app_install.png
      :alt: Slack app installation

   You'll be asked to authorize your new app in your workspace:

   .. image:: img/slack_app_authorize.png
      :alt: Slack app authorization

   Click ``Authorize``.

#. Copy the ``OAuth Access Token`` (e.g., ``xoxp-3168...db0b5``):

   .. image:: img/slack_app_oauth_token.png
      :alt: Slack app OAuth token

   This is what you'll use when creating the ``Slack Workspace Emoji Watcher`` below.

#. If you haven't already, install ``emojiwatch`` into your Django project.
   (See the `Django`_ installation section above.)
   Navigate to your Django project's admin interface and add a new ``Slack Workspace Emoji Watcher`` with your Slack team ID, your OAuth access token, and the Slack channel ID to which you'd like Emojiwatch to post messages:

   .. image:: img/django_add_watcher.png
      :alt: Add a watcher

   Your Slack team ID can be determined by navigating to any channel within your workspace, and looking at ``boot_data.team_id`` in your browser's JavaScript console:

   .. code-block:: console

      >> boot_data.team_id
      "T4P09SCHKT"

   Your Slack channel ID can be found in the URL when navigating to that channel:

   .. code-block:: console

      https://<workspace-name>.slack.com/messages/C8VSYSEQ22/details/
                                                  ^^^^^^^^^^

#. Once your ``Slack Workspace Emoji Watcher`` is saved, you should be able to test your configuration by faking a minimalist ``emoji_changed`` event via ``curl``:

   .. code-block:: sh

      curl --verbose --data '{
        "token": "NS3PYxg1QR1l7s2G0fRDZ8uK",
        "team_id": "T4P09SCHKT",
        "type": "event_callback",
        "event": {
          "type": "emoji_changed",
          "subtype": "add",
          "name": "faked-new-emoji",
          "value": "<some-img-url>"
        }
      }' https://<django-project-base>/emojiwatch/event_hook

   ``<django-project-base>`` is your domain, and optionally any path to your top-level Django project.
   If your Django project provides your root path, this will just be a domain name.
   Assuming everything has been set up correctly so far, this should result in a post to your Slack channel (e.g., ``C8VSYSEQ22``):

   .. image:: img/slack_event_message.png
      :alt: An Emojiwatch post to Slack

   If not, examine the output from your ``curl`` call for any clues as to what went wrong.
   See the `Troubleshooting`_ section below for additional suggestions.

#. Now you're ready to start receiving events.
   Navigate to your Slack app's ``Event Subscriptions`` features section.
   Turn events on and add your Django project's publicly-visible HTTPS URL.
   (This is the same URL you used with your ``curl`` command above.)
   Slack will attempt to post to that URL to verify its accessibility.
   Once verified, subscribe to the ``emoji:read`` event and click ``Save Changes``.

   .. TODO
   .. image:: img/slack_app_events.png
      :alt: Slack app event subscriptions

#. That's it!
   You should now get notices to your designated channel whenever you add or remove custom Emojis to your workspace.

Troubleshooting
+++++++++++++++

   If your ``curl`` command is succeeding, but you're still unable to see a post to your Slack channel, try turning on logging output via your Django settings.
   Here's a minimalist configuration if you don't already have one:

   .. code-block:: python

      import logging
      LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
          'standard': {
            'format': '%(asctime)s\t%(levelname)s\t%(name)s\t%(filename)s:%(lineno)d\t%(message)s',
          },
        },
        'handlers': {
          'default': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
          },
        },
        'loggers': {
          '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False,
          },
          'django': {
            'level': 'INFO',
            'propagate': True,
          },
        },
      }

   Try your ``curl`` command again.
   The Django console log should provide some clue as to what's wrong.

   Some common causes are:

   - Not properly adding or configuring the ``emojiwatch`` app in your Django project.
   - Omitting or using an incorrect value for your ``EMOJIWATCH['slack_verification_token']`` Django setting.
   - Using an incorrect URL for your Django project instance or the ``django-emojiwatch`` event handler.
     (Note: Slack requires event handlers to support HTTPS.)
   - Not creating (or neglecting to save) your ``Slack Workspace Emoji Watcher`` object via your Django project's admin interface.
   - Using incorrect values for your team ID, access token, or channel ID.
   - Failing to properly format a faked ``emoji_changed`` event when invoking ``curl``.

Requirements
------------

You'll need a Slack account (and admin approval) for setting up your Slack app.
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
