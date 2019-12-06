import logging
from collections import ChainMap
from urllib.parse import unquote, quote

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

logger = logging.getLogger('server')

NOOP = lambda *args, **kwargs: None


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

def encode_url(url):
    if url == unquote(url):
        return quote(url.encode('utf-8'), safe='~@#$&()*!+=:;,.?/\'')
    else:
        return url


def quote_url(url):
    return encode_url(unquote(url).decode('utf-8'))


def merge_dicts(*dicts):
    all_keys = set(k for d in dicts for k in d.keys())
    chain_map = ChainMap(*reversed(dicts))
    return {k: chain_map[k] for k in all_keys}


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        key = (cls, str(args), str(kwargs))
        if key not in cls._instances:
            # print ('Instantiating {} {} {}'.format(cls, str(args), str(kwargs)))
            cls._instances[key] = super(Singleton, cls).__call__(*args, **kwargs)

        # print ('Returning {}'.format(cls))
        return cls._instances[key]

class RepositoryMixin:
    def initialize(self, context, asynch=True):
        for key, repository in context.repositories.items():
            repo = repository if asynch else context.db[key]

            self.__setattr__(key + '_repository', repo)
            self.__setattr__(key + '_model', context.models[key])

