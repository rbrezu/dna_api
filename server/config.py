from os.path import expanduser

import derpconf.config as config
from derpconf.config import Config

home = expanduser("~")

Config.allow_environment_variables()

Config.define('SERVER_URL', 'http://dna.whiteosftware.ro', 'SERVER_URL', 'Server url')

Config.define('SERVER_LOG_CONFIG', None, 'Logging configuration as json', 'Logging')
Config.define(
    'SERVER_LOG_FORMAT', '%(asctime)s %(name)s:%(levelname)s %(message)s',
    'Log Format to be used by SERVER when writing log messages.', 'Logging')

Config.define(
    'SERVER_LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S',
    'Date Format to be used by SERVER when writing log messages.', 'Logging')

# DATABASE
Config.define(
    'MONGODB_URL', 'mongodb://localhost:27017/',
    'MONGODB_URL', 'mongodb url')

Config.define(
    'MONGODB_DATABASE', 'dnaAPI',
    'mongodb database', 'mongodb database')

# MODELS OPTIONS
Config.define(
    'REPOSITORIES', {},
    'List of detectors that SERVER should use to find faces and/or features. All of them must be ' +
    'full names of python modules (python must be able to import it)', 'MODELS')

Config.define(
    'MODELS', {},
    'List of detectors that SERVER should use to find faces and/or features. All of them must be ' +
    'full names of python modules (python must be able to import it)', 'MODELS')

# INDEX OPTIONS

Config.define(
    'INDEX_DIR', '/Users/razvan.brezulianu/Projects/PeopleAPI/data',
    'Custom index path directory.'
)


Config.define(
    'APP_CLASS', 'server.app.Application',
    'Custom app class to override SERVERServiceApp. This config value is overridden by the -a command-line parameter.'
)


def generate_config():
    config.generate_config()


def format_value(value):
    if isinstance(value, str):
        return "'%s'" % value
    if isinstance(value, (tuple, list, set)):
        representation = '[\n'
        for item in value:
            representation += '#    %s' % item
        representation += '#]'
        return representation
    return value


if __name__ == '__main__':
    generate_config()
