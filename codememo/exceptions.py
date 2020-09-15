__all__ = [
    'FileLoadingException',
    'NodeRemovalException',
    'NodeReferenceException',
]


class FileLoadingException(Exception):
    pass


class NodeRemovalException(Exception):
    pass


class NodeReferenceException(Exception):
    pass
