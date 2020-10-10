__all__ = ['IOWrapper', 'PygletIOWrapper', 'ShortcutRegistry']


class IOWrapper(object):
    def __init__(self, io):
        self.io = io

    def is_key_pressed(self, key):
        raise NotImplementedError


class PygletIOWrapper(IOWrapper):
    def __init__(self, io):
        super(PygletIOWrapper, self).__init__(io)

    def is_key_pressed(self, key):
        key = key.lower()
        if key in ['ctrl', 'super', 'alt', 'shift']:
            return getattr(self.io, f'key_{key.lower()}')
        else:
            return self.io.keys_down[ord(key)]


class ShortcutRegistry(object):
    def __init__(self, io):
        if not isinstance(io, IOWrapper):
            raise TypeError(f'`io` should be an instance of {IOWrapper}')
        self.io = io
        self.registry = {}

        # used to store name of triggered shortcuts
        self.triggered_shortcuts = set()
        # used to store name of edge-triggered shortcuts
        self.edge_triggered_shortcuts = set()
        # used to store name of edge-triggered shortcuts that have been triggered
        self.prev_edge_triggered_shortcuts = set()

    @property
    def has_triggered_shortcuts(self):
        return len(self.triggered_shortcuts) != 0

    def poll(self):
        """Iterate all registered shortcuts and check whether they are triggered."""
        for name in self.registry:
            if self.is_triggered(name):
                if name in self.edge_triggered_shortcuts & self.prev_edge_triggered_shortcuts:
                    # it's an edge-triggered shortcut and it has been triggered
                    continue
                else:
                    # it's not an edge-triggered shortcut, so it can be triggered repeatedly
                    self.triggered_shortcuts.add(name)
            else:
                # reset cache for edge-triggered shortcut
                if name in self.edge_triggered_shortcuts & self.prev_edge_triggered_shortcuts:
                    self.prev_edge_triggered_shortcuts.remove(name)

    def clear(self):
        for name in self.registry:
            # If there is any edge-triggered shortcut was triggered, store them into
            # `prev_edge_triggered_shortcuts` to avoid them being triggered repeatedly.
            if name in self.edge_triggered_shortcuts & self.triggered_shortcuts:
                self.triggered_shortcuts.remove(name)
                self.prev_edge_triggered_shortcuts.add(name)
        self.triggered_shortcuts.clear()

    def register(self, name, key_bindings, is_edge_triggered=True):
        """Register shortcut.

        Parameters
        ----------
        name : str
            Name of shortcut.
        key_bindings : list of str
            Combination of keys for shortcut.
        is_edge_triggered : bool, optional
            If true, this shortcut can only be triggered when keys are pressed down,
            and it won't be triggered repeatedly when keys are hold.
        """
        if name in self.registry:
            raise ValueError(f'shortcut for `{name}` has already been registered.')
        if not isinstance(key_bindings, list):
            raise TypeError(f'`key_bindings` should be a combination of keys (string)')
        key_bindings = [v.lower() for v in key_bindings]
        if len(set(key_bindings)) < len(key_bindings):
            raise ValueError(f'duplicate keys detected in `key_bindings`')

        self.registry.update({name: key_bindings})
        if is_edge_triggered:
            self.edge_triggered_shortcuts.add(name)

    def unregister(self, name):
        if name not in self.registry:
            raise ValueError(f'shortcut for `{name}` has not yet been registered.')
        self.registry.remove(name)
        if name in self.edge_triggered_shortcuts:
            self.edge_triggered_shortcuts.remove(name)

    def is_triggered(self, name):
        if name not in self.registry:
            raise ValueError(f'shortcut for `{name}` has not yet been registered.')
        return all([self.io.is_key_pressed(k) for k in self.registry[name]])
