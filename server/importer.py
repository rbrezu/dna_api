import inspect
from functools import reduce

from server.utils import logger


def import_class(name, get_module=False):
    module_name = get_module and name or '.'.join(name.split('.')[:-1])
    klass = name.split('.')[-1]

    module = get_module and __import__(name) or __import__(module_name)
    if '.' in module_name:
        module = reduce(getattr, module_name.split('.')[1:], module)

    return get_module and module or getattr(module, klass)


class Importer:
    '''Importer class to import custom classes into context declared from conf file'''

    def __init__(self, config):
        self.config = config
        self.loader = None
        self.repositories = {}
        self.models = {}

    def import_class(self, name, get_module=False):
        return import_class(name, get_module)

    def import_modules(self):
        self.import_item('REPOSITORIES', 'Repositories', is_dictionary=True)
        self.import_item('MODELS', 'Models', is_dictionary=True)

    def import_item(self, config_key=None, class_name=None, is_dictionary=False, is_multiple=False, item_value=None,
                    ignore_errors=False, is_module=False):
        if item_value is None:
            conf_value = getattr(self.config, config_key)
        else:
            conf_value = item_value

        if is_module:
            modules = []
            if conf_value:
                for module_name in conf_value:
                    try:
                        module = __import__(module_name)
                        if '.' in module_name:
                            module = reduce(getattr, module_name.split('.')[1:], module)

                        for name in dir(module):
                            obj = getattr(module, name)
                            if inspect.isclass(obj) and type(obj) == type:
                                modules.append(obj)
                    except ImportError as e:
                        if ignore_errors:
                            logger.warn('Module %s could not be imported: %s', module_name, e)
                        else:
                            raise
            setattr(self, config_key.lower(), tuple(modules))
        elif is_dictionary:
            modules = {}
            if conf_value:
                for key, module_name in conf_value.items():
                    try:
                        module = self.import_class(module_name)
                        modules[key] = (module)
                    except ImportError as e:
                        if ignore_errors:
                            logger.warn('Module %s could not be imported: %s', module_name, e)
                        else:
                            raise
            setattr(self, config_key.lower(), dict(modules))
        elif is_multiple:
            modules = []
            if conf_value:
                for module_name in conf_value:
                    try:
                        if class_name is not None:
                            module = self.import_class('%s.%s' % (module_name, class_name))
                        else:
                            module = self.import_class(module_name, get_module=True)
                        modules.append(module)
                    except ImportError as e:
                        if ignore_errors:
                            logger.warn('Module %s could not be imported: %s', module_name, e)
                        else:
                            raise
            setattr(self, config_key.lower(), tuple(modules))
        else:
            if class_name is not None:
                module = self.import_class('%s.%s' % (conf_value, class_name))
            else:
                module = self.import_class(conf_value, get_module=True)
            setattr(self, config_key.lower(), module)
