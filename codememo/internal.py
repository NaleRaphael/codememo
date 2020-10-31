__all__ = ['GlobalState']


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GlobalState(metaclass=Singleton):
    def __init__(self):
        self._content = {}
        self._error_stack = []

    def __repr__(self):
        return str(self._content)

    def __contains__(self, key):
        return key in self._content

    @property
    def error_occured(self):
        return len(self._error_stack) != 0

    def get(self, *args):
        return self._content.get(*args)

    def pop(self, *args):
        return self._content.pop(*args)

    def set(self, key, value):
        self._content.update({key: value})

    def delete(self, key):
        del self._content[key]

    def push_error(self, error_object):
        self._error_stack.append(error_object)

    def pop_error(self):
        return self._error_stack.pop(-1)
