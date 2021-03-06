# Generated by Django 2.0.2 on 2018-02-27 19:48

import django.core.validators
from django.db import migrations, models
import fernet_fields.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SlackWorkspaceEmojiWatcher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_version', models.IntegerField(default=-2147483648)),
                ('team_id', models.CharField(default='T', max_length=63, unique=True, validators=[django.core.validators.RegexValidator('\\AT[0-9A-Z]+\\Z', message='Must be of the format (e.g.) T123ABC...')], verbose_name='Team ID')),
                ('access_token', fernet_fields.fields.EncryptedCharField(default='xoxa-', max_length=255, validators=[django.core.validators.RegexValidator('^xox[abp](-[0-9A-Fa-f]+)+', message='Must be of the format (e.g.) xoxa-1f2e3d-4c5b6a...')], verbose_name='Access Token')),
                ('channel_id', models.CharField(default='C', max_length=63, validators=[django.core.validators.RegexValidator('\\AC[0-9A-Z]+\\Z', message='Must be of the format (e.g.) C123ABC...')], verbose_name='Channel ID')),
                ('icon_emoji', models.CharField(default=':robot_face:', max_length=255, validators=[django.core.validators.RegexValidator('\\A:[\\w-]+:\\Z', message='Must be of the format (e.g.) :emoji_name:...')], verbose_name='Icon Emoji')),
                ('notes', fernet_fields.fields.EncryptedTextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Slack Workspace Emoji Watcher',
            },
        ),
    ]
