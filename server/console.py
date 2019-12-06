import argparse

from server.context import ServerParameters


def get_server_parameters(arguments=None):
    if arguments is None:
        arguments = []

    parser = argparse.ArgumentParser(description='Server')

    parser.add_argument(
        '-p', '--port', default=8888, type=int,
        help="The port to run this server instance at [default: %(default)s]."
    )

    parser.add_argument(
        '-i', '--ip', default='0.0.0.0',
        help="The host address to run this server instance at [default: %(default)s]."
    )

    parser.add_argument(
        '-f', '--fd',
        help="The file descriptor number or path to listen for connections on (--port and --ip will be ignored if this is set)"
             "[default: %(default)s]."
    )

    parser.add_argument(
        '-c', '--conf', default=None,
        help="The path of the configuration file to use for this server instance [default: %(default)s]."
    )

    parser.add_argument(
        "-l", "--log-level", default="warning",
        help="The log level to be used. Possible values are: debug, info, warning, error, critical or notset. "
             "[default: %(default)s]."
    )

    parser.add_argument(
        "-a", "--app", default='server.app.LandmarkServiceApp',
        help="A custom app to use for this server in case you subclassed [default: %(default)s]."
    )

    parser.add_argument(
        "-d", "--debug", default=False, action='store_true',
        help="Debug mode [default: %(default)s]."
    )

    options = parser.parse_args(arguments)

    return ServerParameters(port=options.port,
                            ip=options.ip,
                            config_path=options.conf,
                            log_level=options.log_level,
                            app_class=options.app,
                            debug=options.debug,
                            fd=options.fd)
