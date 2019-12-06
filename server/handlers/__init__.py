import datetime
import json
import traceback

import tornado.web
from tornado import gen
from tornado.log import app_log
from tornado.web import HTTPError

from server.context import Context
from server.json_encoder import Encoder
from server.model import ValidatorError
from server.utils import logger, RepositoryMixin, str2bool

try:
    basestring  # Python 2
except NameError:
    basestring = str  # Python 3

class BaseHandler(tornado.web.RequestHandler):
    """
    Base handler that sets up all the methods and functions for
    further customization of the tornado request handler logic.

     - ability to add metrics by the on_start and on_finish method
     - prepare method that is called always before calling a
     get/post/delete/put/option request
     - ovveride _execute method such that custom code may be run
     - authorization may be added in the _execute method and a principal object
     could be then passed in the context
    """

    def prepare(self, *args, **kwargs):
        pass

    def on_start(self):
        if not hasattr(self, 'context'):
            return

        self._response_start = datetime.datetime.now()

    @gen.coroutine
    def _execute(self, transforms, *args, **kwargs):
        try:
            self._transforms = transforms
            """Executes this request with the given output transforms."""

            if self.request.method not in self.SUPPORTED_METHODS:
                raise HTTPError(405)

            self.path_args = [self.decode_argument(arg) for arg in args]
            self.path_kwargs = dict((k, self.decode_argument(v, name=k))
                                    for (k, v) in kwargs.items())
            # If XSRF cookies are turned on, reject form submissions without
            # the proper cookie
            if self.request.method not in ("GET", "HEAD", "OPTIONS") and \
                    self.application.settings.get("xsrf_cookies"):
                self.check_xsrf_cookie()

            method = getattr(self, self.request.method.lower())
            self.on_start()

            # AUTH ENABLED
            # _jwt_required(self,
            #               getattr(method, '_authorization_roles', [r.value for r in Role]),
            #               getattr(method, '_authorization_enabled', False))

            result = self.prepare(*self.path_args, **self.path_kwargs)
            if result is not None:
                result = yield result
            if self._prepared_future is not None:
                # Tell the Application we've finished with prepare()
                # and are ready for the body to arrive.
                self._prepared_future.set_result(None)
            if self._finished:
                return

            result = method(*self.path_args, **self.path_kwargs)
            if result is not None:
                result = yield result
            if self._auto_finish and not self._finished:
                self.finish()
        except Exception as e:
            try:
                self._handle_request_exception(e)
            except Exception:
                app_log.error("Exception in exception handler", exc_info=True)
            if (self._prepared_future is not None and
                    not self._prepared_future.done()):
                # In case we failed before setting _prepared_future, do it
                # now (to unblock the HTTP server).  Note that this is not
                # in a finally block to avoid GC issues prior to Python 3.4.
                self._prepared_future.set_result(None)

    def on_finish(self, *args, **kwargs):
        super(BaseHandler, self).on_finish(*args, **kwargs)

        if not hasattr(self, 'context'):
            return

        # total_time = (datetime.datetime.now() - self._response_start).total_seconds() * 1000
        # status = self.get_status()
        ## HERE WE CAN LOG METRICS AS REQUEST STATUS AND TOTAL_TIME


class ContextHandler(BaseHandler, RepositoryMixin):
    """
    Context handler that initializes the application context for each
    application request.
    """

    def initialize(self, context):
        self.context = Context(
            server=context.server,
            config=context.config,
            importer=context.modules.importer,
            request_handler=self
        )
        RepositoryMixin.initialize(self, self.context)

        self.remote_ip = self.request.headers.get('X-Forwarded-For',
                                                  self.request.headers.get('X-Real-Ip', self.request.remote_ip))

    def log_exception(self, *exc_info):
        if isinstance(exc_info[1], tornado.web.HTTPError):
            # Delegate HTTPError's to the base class
            # We don't want these through normal exception handling
            return super(ContextHandler, self).log_exception(*exc_info)

        msg = traceback.format_exception(*exc_info)
        logger.error('ERROR: %s' % "".join(msg))


class ApiHandler(ContextHandler):
    """
    Api Handler class that keeps pagination, sorting and limit parameters
    and sets default headers for json REST API and custom error handling
    """

    def initialize(self, context):
        ContextHandler.initialize(self, context)

        self.limit_default = 20

    def compute_etag(self):
        return None

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def get_sort(self):
        splitted = self.get_argument('sort', None).split(',')
        return (
            splitted[0],
            -1 if splitted[1] == 'desc' else 1
        )

    def write_error(self, status_code, **kwargs):
        error = {'code': status_code,
                 'message': self._reason,
                 }

        lines = ""
        if 'exc_info' in kwargs:
            for line in traceback.format_exception(*kwargs['exc_info']):
                lines += line

            _, exception, _ = kwargs['exc_info']

            if isinstance(exception, ValidatorError):
                error.update({'validator_errors': exception.validator_errors})


        if self.context.server.debug:
            error.update({'stacktrace': lines})

        self.write(json.dumps({'error': error}, cls=Encoder))
        self.finish()

    def prepare(self, *args, **kwargs):
        super(ApiHandler, self).prepare(*args, **kwargs)

        self.limit = int(self.get_argument('limit', self.limit_default))
        self.skip = int(self.get_argument('skip', 0))
        self.sort = self.get_sort() if self.get_argument('sort', None) else None

    def write_json(self, object, status=200):
        self.set_status(status)
        self.write(json.dumps(object, cls=Encoder))


class CrudHandler(ApiHandler):
    """
    CRUD repository
    """

    def prepare(self, *args, **kwargs):
        super(CrudHandler, self).prepare(*args, **kwargs)
        repository = kwargs.get('repository')

        if not hasattr(self, '{}_repository'.format(repository)):
            raise tornado.web.HTTPError(405)

        self.query = json.loads(self.get_argument('_query', '{}'))
        self.just_one = str2bool(self.get_argument('just_one', 'false'))

        self.model, self.repo = self.context.models[repository], self.context.repositories[repository]

    @gen.coroutine
    def get(self, repository):
        if not self.just_one:
            count = yield self.repo.count(self.query)
            self.set_header('X-Total-Count', count)

        result = yield self.repo.find(self.query, self.just_one, self.sort, self.limit, self.skip)
        self.write_json(result)

    @gen.coroutine
    def post(self, repository):
        result = yield self.repo.save(
            self.model.from_json(self.request.body.decode('utf-8'),
                                 validate=True))

        self.write_json(result, status=201)

    @gen.coroutine
    def put(self, repository):
        result = yield self.repo.update(
            self.model.from_json(self.request.body.decode('utf-8'),
                                 validate=True))

        self.write_json(result)

    @gen.coroutine
    def delete(self, repository):
        query = json.loads(self.get_argument('_query', '{}'))
        result = yield self.repo.remove(query)

        self.write_json(result)


class IndexHandler(ContextHandler):
    """
    Handler that serves the index.html template
    """

    def prepare(self, *args, **kwargs):
        super(ContextHandler, self).prepare(*args, **kwargs)

        list = [q.split(',') for q in self.request.headers['Accept'].split(';')]
        mime_types = [item.strip() for sublist in list for item in sublist]

        accepted_mimes = ['text/html', '*/*', 'text/css', 'application/javascript', 'text/javascript']
        if not any(elem in mime_types for elem in accepted_mimes):
            raise HTTPError(406, reason='Bad Accept header')

    def get(self):
        template = self.context.template_manager.get_template('index.html')

        self.set_header('Content-Type', 'text/html')
        self.finish(template.render())
