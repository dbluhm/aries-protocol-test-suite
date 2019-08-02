""" Decorator Schemas and types. """

from schema import And, Use, Optional
from . import MessageSchema

THREAD_SCHEMA = MessageSchema({
    'thid': str,
    Optional('pthid'): str,
    Optional('sender_order'): int,
    Optional('received_orders'): {
        str: int
    }
})

ACK = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification/1.0/ack'
ACK_SCHEMA = MessageSchema({
    'status': And(
        str,
        Use(str.lower),
        lambda s: s in ['ok', 'pending', 'fail']
    ),
    '~thread': THREAD_SCHEMA,
    str: object
})
