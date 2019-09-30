""" Manual Connection Protocol tests.
"""

import pytest
from ariespython import did

from . import (
    parse_invite,
    build_request,
    build_invite,
    invite_to_url,
    build_response,
    RESPONSE_SCHEMA_POST_SIG_VERIFY,
    RESPONSE_SCHEMA_PRE_SIG_VERIFY,
    REQUEST_SCHEMA,
    RESPONSE,
    REQUEST,
)


@pytest.mark.features("core.manual", "connection.manual")
@pytest.mark.priority(10)
@pytest.mark.asyncio
async def test_connection_started_by_tested_agent(config, agent):
    """ Test a connection as started by the agent under test """
    invite_url = input('Input generated connection invite: ')

    invite_msg = parse_invite(invite_url)

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
    print("Awaiting response from tested agent...")
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


@pytest.mark.features("core.manual", "connection.manual")
@pytest.mark.priority(10)
@pytest.mark.asyncio
async def test_connection_started_by_suite(config, agent):
    """ Test a connection as started by the suite. """
    label = 'test-suite-connection-started-by-suite'

    connection_key = await did.create_key(agent.wallet_handle, {})

    invite_str = invite_to_url(build_invite(
        label,
        connection_key,
        config.endpoint
    ), config.endpoint)

    print("\n\nInvitation encoded as URL: ", invite_str)

    print("Awaiting request from tested agent...")
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
