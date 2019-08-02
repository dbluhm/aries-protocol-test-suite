import re
import base64
import uuid
from schema import Optional
from agent_core.message import Message
from .. import MessageSchema

CONNECTION_ACK = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/ack'
DIDDOC_SCHEMA = MessageSchema({
    "@context": "https://w3id.org/did/v1",
    "id": str,
    "publicKey": [{
        "id": str,
        "type": "Ed25519VerificationKey2018",
        "controller": str,
        "publicKeyBase58": str
    }],
    "service": [{
        "id": str,
        "type": "IndyAgent",
        "recipientKeys": [str],
        "routingKeys": [str],
        "serviceEndpoint": str,
    }],
})

CREATE_INVITE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/create_invitation'
CREATE_INVITE_SCHEMA = MessageSchema({
    '@type': CREATE_INVITE,
    '@id': str
})

INVITE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation'
INVITE_SCHEMA = MessageSchema({
    '@type': INVITE,
    '@id': str,
    'label': str,
    'recipientKeys': [str],
    'routingKeys': [str],
    'serviceEndpoint': str,
})

REQUEST = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/request'
REQUEST_SCHEMA = MessageSchema({
    '@type': REQUEST,
    '@id': str,
    'label': str,
    'connection': {
        'DID': str,
        'DIDDoc': DIDDOC_SCHEMA
    }
})


RESPONSE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/response'
RESPONSE_SCHEMA_PRE_SIG_VERIFY = MessageSchema({
    '@type': RESPONSE,
    '@id': str,
    '~thread': {
        'thid': str,
        Optional('sender_order'): int
    },
    'connection~sig': object
})

RESPONSE_SCHEMA_POST_SIG_VERIFY = MessageSchema({
    '@type': RESPONSE,
    '@id': str,
    '~thread': {
        'thid': str,
        Optional('sender_order'): int
    },
    'connection': {
        'DID': str,
        'DIDDoc': DIDDOC_SCHEMA
    }
})


def parse_invite(invite_url: str) -> Message:
    """ Parse an invite url """
    matches = re.match('(.+)?c_i=(.+)', invite_url)
    assert matches, 'Improperly formatted invite url!'

    invite_msg = Message.deserialize(
        base64.urlsafe_b64decode(matches.group(2)).decode('ascii')
    )

    INVITE_SCHEMA.validate(invite_msg)

    return invite_msg

def build_invite(label: str, connection_key: str, endpoint: str) -> str:
    return Message({
        '@type': INVITE,
        'label': label,
        'recipientKeys': [connection_key],
        'serviceEndpoint': endpoint,
        'routingKeys': []
    })


def invite_to_url(invite: Message) -> str:
    b64_invite = base64.urlsafe_b64encode(
        bytes(invite.serialize(), 'utf-8')
    ).decode('ascii')

    return '{}?c_i={}'.format(endpoint, b64_invite)



def build_request(
        label: str,
        my_did: str,
        my_vk: str,
        endpoint: str
        ) -> Message:
    """ Construct a connection request. """
    return Message({
        '@type': REQUEST,
        '@id': str(uuid.uuid4()),
        'label': label,
        'connection': {
            'DID': my_did,
            'DIDDoc': {
                "@context": "https://w3id.org/did/v1",
                "id": my_did,
                "publicKey": [{
                    "id": my_did + "#keys-1",
                    "type": "Ed25519VerificationKey2018",
                    "controller": my_did,
                    "publicKeyBase58": my_vk
                }],
                "service": [{
                    "id": my_did + ";indy",
                    "type": "IndyAgent",
                    "recipientKeys": [my_vk],
                    "routingKeys": [],
                    "serviceEndpoint": endpoint,
                }],
            }
        }
    })


def build_response(
        req_id: str,
        my_did: str,
        my_vk: str,
        endpoint: str
        ) -> Message:
    return Message({
        '@type': RESPONSE,
        '@id': str(uuid.uuid4()),
        '~thread': {
            'thid': req_id,
            'sender_order': 0
        },
        'connection': {
            'DID': my_did,
            'DIDDoc': {
                "@context": "https://w3id.org/did/v1",
                "id": my_did,
                "publicKey": [{
                    "id": my_did + "#keys-1",
                    "type": "Ed25519VerificationKey2018",
                    "controller": my_did,
                    "publicKeyBase58": my_vk
                }],
                "service": [{
                    "id": my_did + ";indy",
                    "type": "IndyAgent",
                    "recipientKeys": [my_vk],
                    "routingKeys": [],
                    "serviceEndpoint": endpoint,
                }],
            }
        }
    })
