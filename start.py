import asyncio
import sys
import logging
import logging.config

import os
import socket
from os.path import expanduser, dirname

import json

import tornado.ioloop
from tornado.httpserver import HTTPServer

from tornado.options import options, define

from server.config import Config
from server.console import get_server_parameters
from server.importer import Importer
from server.context import Context
from server.utils import logger


def get_as_integer(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def get_config(config_path):
    lookup_paths = [os.curdir,
                    expanduser('~'),
                    '/etc/',
                    dirname(__file__)]

    conf = Config.load(config_path, conf_name='application.conf', lookup_paths=lookup_paths)
    logger.debug(json.dumps(conf.items, indent=4))
    return conf


def configure_log(config, log_level):
    if (config.SERVER_LOG_CONFIG and config.SERVER_LOG_CONFIG != ''):
        logging.config.dictConfig(config.SERVER_LOG_CONFIG)
    else:
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=config.SERVER_LOG_FORMAT,
            datefmt=config.SERVER_LOG_DATE_FORMAT
        )


def get_importer(config):
    importer = Importer(config)
    importer.import_modules()

    return importer


def get_context(server_parameters, config, importer):
    return Context(
        server=server_parameters,
        config=config,
        importer=importer
    )


def get_application(context):
    return context.modules.importer.import_class(context.app_class)(context)


def initalize_webpack():
    from tornado import autoreload

    try:
        fn = 'webpack-assets.json'
        with open(fn) as f:
            autoreload.watch(fn)

            assets = json.load(f)
            define('ASSETS', assets)
    except IOError:
        pass
    except KeyError:
        pass


def run_server(application, context):

    initalize_webpack()

    server = HTTPServer(application,
                        xheaders=True)

    if context.server.fd is not None:
        fd_number = get_as_integer(context.server.fd)
        if fd_number is None:
            with open(context.server.fd, 'r') as sock:
                fd_number = sock.fileno()

        sock = socket.fromfd(fd_number,
                             socket.AF_INET | socket.AF_INET6,
                             socket.SOCK_STREAM)
        server.add_socket(sock)
    else:
        server.bind(context.server.port, context.server.ip)

    server.start()


def main(arguments=None):
    '''Runs server with the specified arguments.'''

    logging.basicConfig(level=logging.DEBUG)

    if arguments is None:
        arguments = sys.argv[1:]

    server_parameters = get_server_parameters(arguments)
    config = get_config(server_parameters.config_path)
    configure_log(config, server_parameters.log_level.upper())

    importer = get_importer(config)

    with get_context(server_parameters, config, importer) as context:

        application = get_application(context)
        run_server(application, context)
        try:
            logging.debug('server running at %s:%d' % (context.server.ip, context.server.port))
            tornado.ioloop.IOLoop.current().start()
        except KeyboardInterrupt:
            sys.stdout.write('\n')
            sys.stdout.write("-- server closed by user interruption --\n")


if __name__ == "__main__":
    main()
