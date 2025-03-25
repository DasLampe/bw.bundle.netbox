global node

cfg = node.metadata.get('netbox', {})

users = {
    cfg.get('user'): {
        'full_name': 'netbox system user',
        'home': cfg.get('install_path'),
        'gid': cfg.get('group', 'netbox'),
        'shell': '/usr/sbin/nologin',
    }
}

groups = {
    cfg.get('group'): {}
}

downloads = {
    f'/tmp/netbox-{cfg.get('version')}.tar.gz': {
        'url': f'https://github.com/netbox-community/netbox/archive/refs/tags/v{cfg.get('version')}.tar.gz',
        'sha256': cfg.get('checksum_sha256'),
        'unless': f'test -f /tmp/netbox-{cfg.get('version')}.tar.gz',
    }
}

actions = {
    'unpack_netbox': {
        'command': f'tar xfz /tmp/netbox-{cfg.get('version')}.tar.gz -C /opt',
        'needs': [
            f'download:/tmp/netbox-{cfg.get('version')}.tar.gz',
        ],
        'triggers': [
            'action:chown_netbox_folders',
        ],
        'unless': f'test -d /opt/netbox-{cfg.get("version")}',
    },
    'chown_netbox_folders': {
        'command': f'chown -R {cfg.get('user')} /opt/netbox-{cfg.get("version")}',
        'needs': [
            f'user:{cfg.get('user')}',
        ],
        'triggered': True,
        'triggers': [
            'action:netbox_upgrade.sh',
        ]
    },
    'netbox_upgrade.sh': {
        'command': f'{cfg.get('install_path')}/upgrade.sh',
        'needs': [
            'action:chown_netbox_folders',
            'pkg_apt:',
            f'file:{cfg.get("install_path")}/netbox/netbox/configuration.py',
        ],
        'triggered': True,
        'triggers': [
            'action:create_netbox_superuser',
        ],
        'after': [],
    },
    'create_netbox_superuser': {
        'command': f'. {cfg.get('install_path')}/venv/bin/activate;'
                   f'DJANGO_SUPERUSER_PASSWORD={cfg.get('superuser').get('password', repo.vault.password_for(f'user_{cfg.get('superuser').get('username')}_netbox_{node.name}'))}'
                   f'python3 {cfg.get('install_path')}/netbox/manage.py createsuperuser --noinput '
                   f'--username {cfg.get('superuser').get('username')} --email {cfg.get('superuser').get('email')}',
        'triggered': True,
    },
    'systemd_daemon_reload_netbox': {
        'command': f'systemctl daemon-reload',
        'triggered': True,
        'after': [
            'file:',
        ],
    }
}

files = {
    f'{cfg.get('install_path')}/netbox/netbox/configuration.py': {
        'source': 'opt/netbox/netbox/netbox/configuration.py.j2',
        'content_type': 'jinja2',
        'context': {
            'cfg': cfg,
        },
        'owner': cfg.get('user'),
        'group': cfg.get('group'),
        'needs': [
            f'symlink:{cfg.get('install_path')}',
        ],
        'triggers': [
            'svc_systemd:netbox.service:restart',
        ],
    },
    f'/etc/systemd/system/netbox.service': {
        'source': 'etc/systemd/system/netbox.service.j2',
        'content_type': 'jinja2',
        'context': {
            'cfg': cfg,
        },
        'owner': cfg.get('user'),
        'group': cfg.get('group'),
        'needs':[
            f'symlink:{cfg.get('install_path')}',
        ],
        'triggers': [
            'action:systemd_daemon_reload_netbox',
            'svc_systemd:netbox.service:restart',
        ],
    },
    f'/etc/systemd/system/netbox-rq.service': {
        'source': 'etc/systemd/system/netbox-rq.service.j2',
        'content_type': 'jinja2',
        'context': {
            'cfg': cfg,
        },
        'owner': cfg.get('user'),
        'group': cfg.get('group'),
        'needs':[
            f'symlink:{cfg.get('install_path')}',
        ],
        'triggers': [
            'action:systemd_daemon_reload_netbox',
            'svc_systemd:netbox-rq.service:restart',
        ],
    },
    f'/etc/systemd/system/netbox-housekeeping.service': {
        'source': 'etc/systemd/system/netbox-housekeeping.service.j2',
        'content_type': 'jinja2',
        'context': {
            'cfg': cfg,
        },
        'owner': cfg.get('user'),
        'group': cfg.get('group'),
        'needs':[
            f'symlink:{cfg.get('install_path')}',
        ],
        'triggers': [
            'action:systemd_daemon_reload_netbox',
        ],
    },
    f'/etc/systemd/system/netbox-housekeeping.timer': {
        'source': 'etc/systemd/system/netbox-housekeeping.timer.j2',
        'content_type': 'jinja2',
        'context': {
            'cfg': cfg,
        },
        'owner': cfg.get('user'),
        'group': cfg.get('group'),
        'needs':[
            f'symlink:{cfg.get('install_path')}',
        ],
        'triggers': [
            'action:systemd_daemon_reload_netbox',
            'svc_systemd:netbox-housekeeping.timer:restart',
        ],
    },
}

symlinks = {
    cfg.get('install_path'): {
        'target': f'/opt/netbox-{cfg.get('version')}',
    },
}

svc_systemd = {
    'netbox.service': {
        'enabled': True,
        'running': True,
        'needs': [
            f'file:{cfg.get('install_path')}/netbox/netbox/configuration.py',
            'action:systemd_daemon_reload_netbox',
        ],
    },
    'netbox-rq.service': {
        'enabled': True,
        'running': True,
        'needs': [
            'file:/etc/systemd/system/netbox-rq.service',
            'action:systemd_daemon_reload_netbox',
        ]
    },
    'netbox-housekeeping.service': {
        'enabled': True,
        'running': False, # Triggered by timer
        'needs': [
            'file:/etc/systemd/system/netbox-housekeeping.service',
            'action:systemd_daemon_reload_netbox',
        ]
    },
    'netbox-housekeeping.timer': {
        'enabled': True,
        'running': True,
        'needs': [
            'file:/etc/systemd/system/netbox-housekeeping.timer',
            'action:systemd_daemon_reload_netbox',
        ],
    },
}

if node.has_bundle('postgres'):
    actions['netbox_upgrade.sh']['after'] += [
        'bundle:postgres',
    ]

if node.has_bundle('redis'):
    actions['netbox_upgrade.sh']['after'] += [
        'bundle:redis',
    ]

for plugin,plugin_cfg in cfg.get('plugins', {}).items():
    actions[f'netbox_install_plugin_{plugin}'] = {
        'command': f'echo {plugin_cfg.get('pip_pkg', plugin)} >> local_requirements.txt;'
                   f'. {cfg.get('install_path')}/venv/bin/activate; '
                   f'pip install {plugin_cfg.get('pip_pkg', plugin)} && '
                   f'python3 {cfg.get('install_path')}/netbox/manage.py migrate {plugin} && '
                   f'python3 {cfg.get('install_path')}/netbox/manage.py collectstatic --no-input',
        'needs': [
            'action:netbox_upgrade.sh',
        ],
        'triggers': [
            'svc_systemd:netbox.service:restart',
            'svc_systemd:netbox-rq.service:restart',
        ],
    }
