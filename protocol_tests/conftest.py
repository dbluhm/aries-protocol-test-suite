""" Test Suite fixture definitions.

    These fixtures define the core functionality of the testing agent.

    For more information on how pytest fixtures work, see
    https://docs.pytest.org/en/latest/fixture.html#fixture
"""

import asyncio
import hashlib

import pytest
from ariespython import did

from agent_core.compat import create_task
from . import TestingAgent

# pylint: disable=redefined-outer-name


@pytest.fixture(scope='session')
def event_loop():
    """ Create a session scoped event loop.

        pytest.asyncio plugin provides a default function scoped event loop
        which cannot be used as a dependency to session scoped fixtures.
    """
    return asyncio.get_event_loop()


@pytest.fixture(scope='session')
def config(pytestconfig):
    """ Get suite configuration.
    """
    yield pytestconfig.suite_config

    # TODO: Cleanup?


@pytest.fixture(scope='session')
async def agent(config):
    """ The persistent agent used by the test suite to test other agents """
    test_suite_agent = await TestingAgent.from_config_async(config)
    task = create_task(test_suite_agent.start())

    yield test_suite_agent

    await test_suite_agent.shutdown()
    task.cancel()


@pytest.fixture(scope='session')
async def test_id(config, agent):
    """ Generate the test suite and subject identities. """
    test_did, test_vk = await did.create_and_store_my_did(
        agent.wallet_handle,
        {'seed': hashlib.sha256(b'aries-protocol-test-suite').hexdigest()}
    )

    subject_did, subject_vk = await did.create_and_store_my_did(
        agent.wallet_handle,
        {'seed': hashlib.sha256(b'aries-protocol-test-subject').hexdigest()}
    )

    await did.set_did_metadata(
        agent.wallet_handle,
        subject_did,
        {'service': config['subject']['service']}
    )

    yield test_did, test_vk, subject_did, subject_vk
