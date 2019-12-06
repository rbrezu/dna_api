import tornado
from tornado.web import Application

from server.handlers import IndexHandler, CrudHandler
from server.handlers.sequence import SequenceUploadHandler, SequenceQueryHandler


class Application(tornado.web.Application):
    '''Application server class that holds all routes'''

    def __init__(self, context):
        self.context = context
        self.debug = getattr(self.context.server, 'debug', False)

        handlers = self.get_handlers()
        super(Application, self).__init__(handlers,
                                          debug=False, autoreload=False)

    def get_handlers(self):
        handlers = [
            (r'/api/crud/(?P<repository>\w+)', CrudHandler, {'context': self.context}),
            (r'/api/sequence/upload', SequenceUploadHandler, {'context': self.context}),
            (r'/api/sequence/query', SequenceQueryHandler, {'context': self.context}),

            (r"/assets/img/(.*)", tornado.web.StaticFileHandler, {"path": "dist/assets/img"}),
            (r"/dist/(.*)", tornado.web.StaticFileHandler, {"path": "dist"}),
            (r"/.*", IndexHandler, {'context': self.context}),
        ]

        return handlers

