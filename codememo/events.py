__all__ = ['NodeEvent', 'NodeEventPublisher']


class NodeEvent(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.kwargs = kwargs

    def __repr__(self):
        return f'<NodeEvent "{self.name}">'

    def get(self, name, default=None):
        return self.kwargs.get(name, default)


class NodeEventPublisher(object):
    def __init__(self):
        self.subscribers = []

    def register(self, subscriber):
        self.subscribers.append(subscriber)

    def unregister(self, subscriber):
        try:
            idx = self.subscribers.index(subscriber)
        except ValueError as ex:
            msg = f'Subscriber {subscriber} does not exist in list'
            raise ValueError(msg) from ex
        self.subscribers.pop()

    def dispatch(self, event):
        if not isinstance(event, NodeEvent):
            raise TypeError(f'should be an instance of {NodeEvent}')

        for subscriber in self.subscribers:
            callback_name = f'handle_event__{event.name}'
            callback = getattr(subscriber, callback_name)
            if callback is None:
                raise ValueError(
                    (f'Method {callback_name} does not implemented '
                    f'in subscriber {subscriber}')
                )
            callback(event)
