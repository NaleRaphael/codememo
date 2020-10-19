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
    EDGE_TRIGGER_TYPES = ['positive', 'negative']

    def __init__(self, io):
        if not isinstance(io, IOWrapper):
            raise TypeError(f'`io` should be an instance of {IOWrapper}')
        self.io = io
        self.registry = {}

        # used to store name of triggered shortcut
        self.triggered_shortcut = None
        # used to store name of edge-triggered shortcut
        self.edge_triggered_shortcut = None
        # used to store name of edge-triggered shortcut that have been triggered
        self.prev_edge_triggered_shortcut = None

        # registry of edge-triggered shortcuts; positive: key down, negative: key up
        self.positive_edge_triggered_registry = set()
        self.negative_edge_triggered_registry = set()

    def poll(self):
        """Iterate all registered shortcuts and check whether they are triggered."""
        candidates = []
        for name in self.registry:
            if self.is_pressed(name):
                if name in self.positive_edge_triggered_registry:
                    # if all keys in combination are pressed, we should not trigger it again
                    if not self.prev_edge_triggered_shortcut:
                        self.edge_triggered_shortcut = name
                        candidates.append(name)
                elif name in self.negative_edge_triggered_registry:
                    if not self.edge_triggered_shortcut:
                        self.edge_triggered_shortcut = name
                else:
                    # it's not an edge-triggered shortcut, so it can be triggered repeatedly
                    candidates.append(name)
            else:
                # reset cache for edge-triggered shortcut
                if name == self.prev_edge_triggered_shortcut:
                    self.prev_edge_triggered_shortcut = None
                # negative-edge-triggered (key up)
                if name == self.edge_triggered_shortcut:
                    candidates.append(self.edge_triggered_shortcut)
                    self.prev_edge_triggered_shortcut = self.edge_triggered_shortcut
                    self.edge_triggered_shortcut = None

        if len(candidates) >= 2:
            # handle cases with partially equal key combination, e.g. 'CTRL+S' and `CTRL+SHIFT+S`
            num_key_bindings = [len(self.registry[name]) for name in candidates]
            idx = max(range(len(num_key_bindings)), key=lambda i: num_key_bindings[i])
            self.triggered_shortcut = candidates[idx]
        elif len(candidates) == 1:
            self.triggered_shortcut = candidates[0]

    def clear(self):
        """Clear cached state of triggered shortcut."""
        if self.triggered_shortcut in self.positive_edge_triggered_registry:
            self.prev_edge_triggered_shortcut = self.triggered_shortcut
            self.edge_triggered_shortcut = None

        self.triggered_shortcut = None

    def register(self, name, key_bindings, edge_trigger=None):
        """Register shortcut.

        Parameters
        ----------
        name : str
            Name of shortcut.
        key_bindings : list of str
            Combination of keys for shortcut.
        edge_trigger : str, one of ['positive', 'negative']
            Indicate given shortcut should be triggered only when keys are pressed
            down or released, so that shortcut won't be triggered repeatedly when
            keys are hold. Default is `None` and that means shortcut can be triggered
            repeatedly.
        """
        if name in self.registry:
            raise ValueError(f'shortcut for `{name}` has already been registered.')
        if not isinstance(key_bindings, list):
            raise TypeError(f'`key_bindings` should be a combination of keys (string)')
        key_bindings = [v.lower() for v in key_bindings]
        if len(set(key_bindings)) < len(key_bindings):
            raise ValueError(f'duplicate keys detected in `key_bindings`')

        self.registry.update({name: key_bindings})
        if edge_trigger in self.EDGE_TRIGGER_TYPES:
            if edge_trigger == 'positive':
                self.positive_edge_triggered_registry.add(name)
            elif edge_trigger == 'negative':
                self.negative_edge_triggered_registry.add(name)

    def unregister(self, name):
        if name not in self.registry:
            raise ValueError(f'shortcut for `{name}` has not yet been registered.')
        self.registry.remove(name)
        if name in self.positive_edge_triggered_registry:
            self.positive_edge_triggered_registry.remove(name)
        if name in self.negative_edge_triggered_registry:
            self.negative_edge_triggered_registry.remove(name)

    def is_pressed(self, name):
        if name not in self.registry:
            raise ValueError(f'shortcut for `{name}` has not yet been registered.')
        return all([self.io.is_key_pressed(k) for k in self.registry[name]])
