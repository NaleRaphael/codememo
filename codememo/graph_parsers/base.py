__all__ = ['BaseParser']


class BaseParser(object):
    def __init__(self):
        pass

    def parse(self, fn):
        raise NotImplementedError
