# -*- coding: utf-8 -*-

import inspect
import logging


log = logging.getLogger(__name__)


def is_event(event):
    """Return True if event is a (strict) subclass or an instance of Event."""
    return ((inspect.isclass(event) and issubclass(event, Event)) or isinstance(event, Event)
            and event.type is not None)


_handler_to_event = {}
def on_event(event):  # noqa:E302
    """Mark function or method as a handler for the given event (type)."""

    def decorator(func):
        _handler_to_event[func] = event.type if is_event(event) else event
        return func

    return decorator


class Event(dict):
    """Base class for events."""
    type = None

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getattr__(self, name):
        return self[name]


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
            if obj in _handler_to_event:
                members = (('', obj),)
            else:
                members = (m for m in inspect.getmembers(obj))

            for name, method in members:
                if name.startswith('__'):
                    continue

                event = _handler_to_event.get(method)
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
                    except Exception as exc:
                        log.error("Unhandled exception in event handler %r: %s", handler, exc)


def _test():
    class KeyEvent(Event):
        type = 'key'

    def handle_key(e):
        print("Function handler for {type} event (key={key})".format(type=e.type, key=e.key))

    @on_event('click')
    def handle_click(e):
        print("Function handler for {type} event (pos={pos})".format(type=e.type, pos=e.pos))

    class Handler:
        @on_event('key')
        def handle_key(self, e):
            print("Method handler for {type} event (key={key})".format(type=e.type, key=e.key))

        @on_event('click')
        def handle_click(self, e):
            print("Method handler for {type} event (pos={pos})".format(type=e.type, pos=e.pos))
            return True  # Do not propagate event further up the handler stack

    dispatcher = EventDispatcher()
    dispatcher.push_handlers(handle_click, key=handle_key)
    dispatcher.push_handlers(Handler())
    print(_handler_to_event)

    key_event = KeyEvent(key='a')
    click_event1 = Event(type='click', pos=(23, 42))
    dispatcher.dispatch(key_event, click_event1)
    dispatcher.pop_handlers()
    click_event2 = Event(type='click', pos=(99, 66))
    dispatcher.dispatch(click_event2)


if __name__ == '__main__':
    _test()
