# -*- coding: utf-8 -*-
"""
    __main__.py

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import click
from trytond.config import CONFIG


@click.command()
@click.option('--config', '-c', help='Path to tryton configuration file')
@click.argument('host', default='0.0.0.0')
@click.argument('port', default=9000)
@click.option('--debug', default=False, is_flag=True)
@click.option(
    '--threaded/--not-threaded', default=True,
    help="should the process handle each request in a separate thread?")
def run(config, host, port, debug, threaded):
    """
    Runs the application on a local development server.
    """
    if config:
        CONFIG.update_etc(config)

    if hasattr(CONFIG, 'set_timezone'):
        CONFIG.set_timezone()

    from application import app
    app.run(host, port, debug=debug, threaded=threaded)


def main():
    """
    Just a wrapper around run to make it easy to use in entry point for console
    script.
    """
    run(auto_envvar_prefix='TRYTOND')


if __name__ == '__main__':
    main()
