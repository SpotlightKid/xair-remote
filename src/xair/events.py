# -*- coding: utf-8 -*-

import inspect
import logging

from collections import OrderedDict


log = logging.getLogger(__name__)


def is_event(event):
    """Return True if event is a (strict) subclass or an instance of Event."""
    return ((inspect.isclass(event) and issubclass(event, Event)) or isinstance(event, Event)
            and event.type is not None)


def on_event(event):
    """Mark function or method as a handler for the given event (type)."""

    def decorator(func):
        func._handler_for = event.type if is_event(event) else event
        return func

    return decorator


class Bunch(dict):
    """A generic container object with unified attribute and dict-style access to its members."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class Registrable(type):
    """Meta-class for registrable and sub-classes.

    Holds a registry of all sub-classes.

    """
    registry = OrderedDict()

    def __init__(cls, clsname, bases, classdict):
        type_ = getattr(cls, 'type')
        if type_:
            cls.registry[type_] = cls


class Event(Bunch, metaclass=Registrable):
    """Base class for events."""
    type = None

    @classmethod
    def event_types(cls):
        return cls.registry.keys()


class EventDispatcher:
    """A base class for objects, which can register event handlers and dispatch events.

    Can be also instantiated and used directly without sub-classing.

    """
    def push_handlers(self, *args, **kwargs):
        """Push given event handlers on top of the handler stack.

        Handlers are given as positional or keyword arguments. In the former case, each argument
        should be an object, which has methods that are marked as event handlers with the
        `on_event` decorator. For keyword arguments, the argument name specifies the event
        type (corresponding to the `type` attribute of an `Event` sub-class/instance) and the
        value specifies the handler callable.

        """
        if not hasattr(self, '_handler_stack'):
            self._handler_stack = []

        self._handler_stack.append({})

        for obj in args:
            if hasattr(obj, '_handler_for'):
                members = (('', obj),)
            else:
                members = inspect.getmembers(obj, predicate=inspect.ismethod)

            for name, method in members:
                if name.startswith('__'):
                    continue

                event = getattr(method, '_handler_for', None)
                if event:
                    if isinstance(event, Event) and event.type is not None:
                        event = event.type
                    self._handler_stack[-1][event] = method

        for event, handler in kwargs.items():
            if is_event(event):
                event = event.type
            self._handler_stack[-1][event] = handler

    def pop_handlers(self):
        """Remove the top layer of event handlers from the stack

        :raises IndexError: if the handler stack is empty.

        """
        return getattr(self, '_handler_stack', []).pop()

    def dispatch(self, *events):
        """Dispatch one or more events to all matching handlers on the stack."""
        if not hasattr(self, '_handler_stack'):
            self._handler_stack = []

        for event in events:
            assert isinstance(event, Event)
            # Search handler stack for matching event handlers
            for handlers in reversed(self._handler_stack):
                handler = handlers.get(event.type, None)
                if handler:
                    try:
                        if handler(event):
                            break
                    except:
                        log.exception("Unhandled exception in event handler %r.", handler)


def _test():
    class KeyEvent(Event):
        type = 'key'

    print("Registered event types:", ", ".join(Event.event_types()))

    def handle_key(e):
        print("Function handler for {e.type} event (key={e.key})".format(e=e))

    @on_event('click')
    def handle_click(e):
        print("Function handler for {e.type} event (pos={e.pos})".format(e=e))

    class Handler:
        @on_event('key')
        def handle_key(self, e):
            print("Method handler for {e.type} event (key={e.key})".format(e=e))

        @on_event('click')
        def handle_click(self, e):
            print("Method handler for {e.type} event (pos={e.pos})".format(e=e))
            return True  # Do not propagate event further up the handler stack

    dispatcher = EventDispatcher()
    dispatcher.push_handlers(handle_click, key=handle_key)
    dispatcher.push_handlers(Handler())
    dispatcher.dispatch(KeyEvent(key='a'), Event(type='click', pos=(23, 42)))
    dispatcher.pop_handlers()
    dispatcher.dispatch(Event(type='click', pos=(99, 66)))


if __name__ == '__main__':
    _test()
