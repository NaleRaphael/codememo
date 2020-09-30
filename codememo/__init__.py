# This should be processed first since we might need to load forked `pyimgui`
from . import vendor

from . import config
from . import objects
from . import components
from . import events
from . import exceptions

try:
    from .version import __version__
except:
    # Fallback to this default value if this package is imported but not installed
    __version__ = '0.0.0.dev'


__all__ = ['config', 'objects', 'components', 'events', 'exceptions', 'vendor']
