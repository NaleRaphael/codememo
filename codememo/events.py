from .internal import Singleton

__all__ = ['NodeEvent', 'NodeEventRegistry']


class NodeEvent(object):
    def __init__(self, name, event_args):
        self.name = name
        self.event_args = event_args

    def __repr__(self):
        return f'<NodeEvent "{self.name}">'

    def get(self, name, default=None):
        return self.event_args.get(name, default)


class NodeEventRegistry(metaclass=Singleton):
    def __init__(self):
        self.registry = {}

    @classmethod
    def get_instance(cls):
        return cls()

    def clear(self):
        self.registry = {}

    def register(self, event_name, subscriber):
        if not callable(subscriber):
            raise TypeError('Subscriber should be a callable.')
        if event_name not in self.registry:
            self.registry.update({event_name: []})
        self.registry[event_name].append(subscriber)

    def unregister(self, event_name, subscriber):
        if event_name not in self.registry:
            raise ValueError(f'Event {event_name} has not been registered')
        try:
            idx = self.registry[event_name].index(subscriber)
        except ValueError as ex:
            msg = f'Subscriber {subscriber} does not exist in list'
            raise ValueError(msg) from ex
        self.registry[event_name].pop(idx)

    def dispatch(self, event):
        if not isinstance(event, NodeEvent):
            raise TypeError(f'should be an instance of {NodeEvent}')
        if event.name not in self.registry:
            raise ValueError(f'Event {event.name} has not been subscribed by anyone')

        for subscriber in self.registry[event.name]:
            subscriber(event)
