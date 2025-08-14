
import click
from flask.cli import with_appcontext

@click.group('rbac')
def rbac_group():
    "RBAC helper commands (attach your User model inside your real app)"
