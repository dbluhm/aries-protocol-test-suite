""" Automatic Connection Protocol tests.
"""

import pytest
from ariespython import did

from agent_core.message import Message
from . import (
    build_request,
    build_invite,
    build_response,
    RESPONSE_SCHEMA_POST_SIG_VERIFY,
    RESPONSE_SCHEMA_PRE_SIG_VERIFY,
    REQUEST_SCHEMA,
    INVITE,
    INVITE_SCHEMA,
    RESPONSE,
    REQUEST,
    CONNECTION_ACK,
    CREATE_INVITE
)

from ..decorators import ACK_SCHEMA


@pytest.mark.features("core", "connection", "connection.auto")
@pytest.mark.priority(10)
@pytest.mark.asyncio
async def test_connection_started_by_tested_agent(config, agent, test_id):
    """ Test a connection as started by the agent under test """
    test_did, test_vk, subject_did, subject_vk = test_id

    print('\nRequesting creation of new invite...')
    await agent.send(
        Message({
            '@type': CREATE_INVITE
        }),
        subject_vk,
        from_key=test_vk,
        service=config['subject']['service']
    )

    invite_msg = await agent.expect_message(INVITE, 30)
    INVITE_SCHEMA.validate(invite_msg)

    print("\nReceived Invite:\n", invite_msg.pretty_print())

    # Create my information for connection
    (my_did, my_vk) = await did.create_and_store_my_did(
        agent.wallet_handle,
        {}
    )

    # Send Connection Request to inviter
    request = build_request(
        'test-connection-started-by-tested-agent',
        my_did,
        my_vk,
        config.endpoint
    )

    print("\nSending Request:\n", request.pretty_print())

    await agent.send(
        request,
        invite_msg['recipientKeys'][0],
        from_key=my_vk,
        service={'serviceEndpoint': invite_msg['serviceEndpoint']}
    )

    # Wait for response
    print("Awaiting response from test subject...")
    response = await agent.expect_message(RESPONSE, 30)

    RESPONSE_SCHEMA_PRE_SIG_VERIFY.validate(response)
    print(
        "\nReceived Response (pre signature verification):\n",
        response.pretty_print()
    )

    response['connection'] = \
        await agent.verify_signed_field(response['connection~sig'])
    del response['connection~sig']

    RESPONSE_SCHEMA_POST_SIG_VERIFY.validate(response)
    assert response['~thread']['thid'] == request.id

    print(
        "\nReceived Response (post signature verification):\n",
        response.pretty_print()
    )

    ack = Message({
        '@type': CONNECTION_ACK,
        'status': 'OK',
        '~thread': {'thid': response.id}
    })
    (_, their_vk, their_endpoint) = (
        response['connection']['DIDDoc']['publicKey'][0]['controller'],
        response['connection']['DIDDoc']['publicKey'][0]['publicKeyBase58'],
        response['connection']['DIDDoc']['service'][0]['serviceEndpoint']
    )

    print('\nSending Ack:', ack.pretty_print())
    await agent.send(
        ack,
        their_vk,
        from_key=my_vk,
        service={'serviceEndpoint': their_endpoint}
    )


@pytest.mark.features("core", "connection", "connection.auto", "connection.passive")
@pytest.mark.priority(10)
@pytest.mark.asyncio
async def test_connection_started_by_suite(config, agent, test_id):
    """ Test a connection as started by the suite. """
    label = 'test-suite-connection-started-by-suite'
    test_did, test_vk, subject_did, subject_vk = test_id

    connection_key = await did.create_key(agent.wallet_handle, {})

    invite_msg = build_invite(label, connection_key, config.endpoint)

    print("\n\nSending Invite: ", invite_msg.pretty_print())
    await agent.send(
        invite_msg,
        subject_vk,
        from_key=test_vk,
        service=config['subject']['service']
    )

    print("Awaiting request from test subject...")
    request = await agent.expect_message(REQUEST, 30)

    REQUEST_SCHEMA.validate(request)
    print("\nReceived request:\n", request.pretty_print())

    (_, their_vk, their_endpoint) = (
        request['connection']['DIDDoc']['publicKey'][0]['controller'],
        request['connection']['DIDDoc']['publicKey'][0]['publicKeyBase58'],
        request['connection']['DIDDoc']['service'][0]['serviceEndpoint']
    )

    (my_did, my_vk) = await did.create_and_store_my_did(
        agent.wallet_handle,
        {}
    )

    response = build_response(request.id, my_did, my_vk, config.endpoint)
    print(
        "\nSending Response (pre signature packing):\n",
        response.pretty_print()
    )

    response['connection~sig'] = await agent.sign_field(
        connection_key,
        response['connection']
    )
    del response['connection']
    print(
        "\nSending Response (post signature packing):\n",
        response.pretty_print()
    )

    await agent.send(
        response,
        their_vk,
        from_key=my_vk,
        service={'serviceEndpoint': their_endpoint}
    )

    print("Awaiting ack from test subject...")
    ack = await agent.expect_message(CONNECTION_ACK, 30)
    print("\nReceived ack:\n", ack.pretty_print())

    ACK_SCHEMA.validate(ack)
    assert ack['status'].lower() == 'ok'
    assert ack['~thread']['thid'] == response.id
    assert ack.mtc.ad['sender_vk'] == their_vk
    assert ack.mtc.ad['recip_vk'] == my_vk
