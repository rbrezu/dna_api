import functools
import logging
import sys
import traceback
from asyncio import Future
from concurrent.futures.process import ProcessPoolExecutor

import motor
from jinja2 import Environment, FileSystemLoader
from tornado.ioloop import IOLoop

from server.index.sequence_index import SequenceIndex
from server.utils import Singleton, logger


class Context:
    '''
    Class responsible for containing:
    * Server Configuration Parameters
    * Configurations read from config file
    * Request Parameters
    * Singleton database object

    Each instance of this class MUST be unique per request. This class should not be cached in the server.
    '''

    def __init__(self, server=None, config=None, importer=None, request_handler=None):
        self.server = server
        self.config = config

        if importer:
            self.modules = ContextImporter(self, importer)
        else:
            self.modules = None

        self.app_class = getattr(config, 'APP_CLASS', 'server.app.Application')

        self.request_handler = request_handler
        self.template_manager = TemplateManager('dist')

        self.create_database(importer)
        self.load_indexes()

    def load_indexes(self):
        idx = SequenceIndex()
        idx.load(self.config.INDEX_DIR)

    def create_database(self, importer):
        self.db = Database(self.config.MONGODB_URL, self.config.MONGODB_DATABASE)

        if importer.models:
            self.models = importer.models

        if importer.repositories:
            self.repositories = {key: repository(self.models, self.db, self)
                                 for key, repository in importer.repositories.items()}

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.modules:
            self.modules.cleanup()
        #
        # idx = SequenceIndex()
        # idx.save()

        logging.info('Finished closing off')

    def __repr__(self):
        return 'Context({}, {}, {})'.format(self.server, self.config, self.app_class)


class ServerParameters(object):
    def __init__(self, port, ip, config_path, log_level, app_class, debug=False, fd=None):
        self.port = port
        self.ip = ip
        self.config_path = config_path
        self.log_level = log_level
        self.app_class = app_class
        self.debug = debug
        self.fd = fd


class ContextImporter:
    def __init__(self, context, importer):
        self.context = context
        self.importer = importer

        self.models = importer.models
        self.repositories = importer.repositories

    def cleanup(self):
        pass


class Database(metaclass=Singleton):
    def __init__(self, url, db_name):
        from pymongo import MongoClient

        self.db_name = db_name

        logging.info('Connecting to database {}'.format(url))
        self.motor_client = motor.motor_tornado.MotorClient(url, connectTimeoutMS=4)
        self.pymongo_client = MongoClient(url, connectTimeoutMS=4)

        self.startup()
        # self.changelog_applied = True

    # cleanup hanging jobs
    def startup(self):
        db = self.pymongo_client[self.db_name]
        db.job.drop()

    def __getitem__(self, key):
        return self.db[key]

    @property
    def db(self):
        return self.motor_client[self.db_name]


class TemplateManager(metaclass=Singleton):
    def __init__(self, path):
        if path:
            self.env = Environment(loader=FileSystemLoader(path))
        else:
            self.env = None

    def get_template(self, name):
        return self.env.get_template(name)

class ProcessPoolExecutorStackTracked(ProcessPoolExecutor):

    def submit(self, fn, *args, **kwargs):
        """Submits the wrapped function instead of `fn`"""

        return super(ProcessPoolExecutorStackTracked, self).submit(
            self._function_wrapper, fn, *args, **kwargs)

    def _function_wrapper(self, fn, *args, **kwargs):
        """Wraps `fn` in order to preserve the traceback of any kind of
        raised exception

        """
        try:
            return fn(*args, **kwargs)
        except Exception:
            # Creates an
            # exception of the
            # same type with the
            # traceback as
            # message
            raise sys.exc_info()[0](traceback.format_exc())

