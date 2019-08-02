""" Demonstrate testing framework. """
import asyncio
# import logging

import pytest
from ariespython import did

from agent_core.message import Message
from agent_core.mtc import (
    AUTHENTICATED_ORIGIN,
    CONFIDENTIALITY,
    DESERIALIZE_OK,
    INTEGRITY,
    NONREPUDIATION
)
from . import MessageSchema


@pytest.mark.asyncio
@pytest.mark.features('simple')
async def test_simple_messaging(config, agent, test_id):
    """ Show simple messages being passed to and from tested agent """

    _my_did, my_vk, their_did, their_vk = test_id

    expected_schema = MessageSchema({
        '@type': 'test/protocol/1.0/test',
        '@id': str,
        'msg': 'pong'
    })

    ping = Message({
        '@type': 'test/protocol/1.0/test',
        'msg': 'ping'
    })
    print('Sending message:', ping.pretty_print())
    await agent.send(
        ping,
        their_vk,
        to_did=their_did,
        from_vk=my_vk
    )

    pong = await agent.expect_message('test/protocol/1.0/test', 1)
    print('Received message:', pong.pretty_print())

    assert pong.mtc[
        CONFIDENTIALITY | INTEGRITY | AUTHENTICATED_ORIGIN | DESERIALIZE_OK
    ]
    assert not pong.mtc[NONREPUDIATION]
    assert pong.mtc.ad['sender_vk'] == their_vk
    assert pong.mtc.ad['recip_vk'] == my_vk

    assert expected_schema.validate(pong)
    assert agent.ok()
