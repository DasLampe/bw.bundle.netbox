defaults = {
    'netbox': {
        'version': '4.2.4',
        'checksum_sha256': 'eefeb3eb40abe86163377292960905af9c49699df87d993976bec53d6d0e1407',
        'address': 'localhost',
        'port': 8001,
        'user': 'netbox',
        'group': 'netbox',
        'install_path': '/opt/netbox',
        'allowed_hosts': ['*'],
        'cors_origin_whitelist': [
            #'https://example.org',
        ],
        'db': {
            'host': 'localhost',
            'port': 5432,
            'name': 'netbox',
            'user': 'netbox',
            'password': repo.vault.password_for(f'user_netbox_postgres_{node.name}'),
        },
        'redis': {
            'tasks': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
            },
            'caching': {
                'host': 'localhost',
                'port': 6379,
                'db': 1,
            },
        },
        'secret_key': repo.vault.password_for(f'netbox_secret_key_{node.name}', length=128),
        # 'superuser': {
        #     'username': 'admin',
        #     'email': 'admin@example.org',
        #     'password': repo.vault.password_for(f'netbox_default_superuser_{node.name}'),
        # },
        # 'plugins': {
        #     'netbox_topology_views': {
        #         'pip_pkg': 'netbox-topology-views',
        #         'config': {
        #             'allow_coordinates_saving': True,
        #             'always_save_coordinates': True
        #         },
        #     },
        # }
    },
}

@metadata_reactor
def add_pkg_apt_dependencies(metadata):
    if not node.has_bundle('apt'):
        raise DoNotRunAgain

    return {
        'apt': {
            'packages': {
                'python3': {
                    'installed': True,
                },
                'python3-pip': {
                    'installed': True,
                },
                'python3-venv': {
                    'installed': True,
                },
                'python3-dev': {
                    'installed': True,
                },
                'build-essential': {
                    'installed': True,
                },
                'libxml2-dev': {
                    'installed': True,
                },
                'libxslt1-dev': {
                    'installed': True,
                },
                'libffi-dev': {
                    'installed': True,
                },
                'libpq-dev': {
                    'installed': True,
                },
                'libssl-dev': {
                    'installed': True,
                },
                'zlib1g-dev': {
                    'installed': True,
                },
            },
        },
    }

@metadata_reactor
def add_netbox_postgres_user(metadata):
    if not node.has_bundle('postgres') or not metadata.get('netbox/db/host') == "localhost":
        raise DoNotRunAgain

    return {
        'postgres': {
            'databases': {
                metadata.get('netbox/db/name'): {
                    'owner_name': metadata.get('netbox/db/user'),
                    'owner_password': metadata.get('netbox/db/password'),
                }
            }
        }
    }
