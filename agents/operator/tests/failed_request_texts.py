"""Measured SDK text fixtures for failed operator requests.

Agent: operator
Role: pin complete vendor status messages and both timeout texts.
External I/O: none; fixtures contain no usable credential.
"""

from __future__ import annotations

OPENAI_MESSAGE = (
    "Incorrect API key provided: not-a-ke***q125. You can find your API key at "
    "https://platform.openai.com/account/api-keys."
)
OPENAI_STATUS = (
    "Error code: 401 - {'error': {'message': '"
    + OPENAI_MESSAGE
    + "', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}"
)
ANTHROPIC_STATUS = (
    "Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', "
    "'message': 'invalid x-api-key'}, 'request_id': 'req_011'}"
)
DRAINED_STATUS = (
    "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', "
    "'message': 'Your credit balance is too low to access the Anthropic API.'}, "
    "'request_id': 'req_011'}"
)
STATUS_CASES = (
    (OPENAI_STATUS, "401", OPENAI_MESSAGE),
    (ANTHROPIC_STATUS, "401", "invalid x-api-key"),
    (
        DRAINED_STATUS,
        "400",
        "Your credit balance is too low to access the Anthropic API.",
    ),
)
TIMEOUT_TEXTS = (
    "Request timed out.",
    "Request timed out or interrupted. This could be due to a network timeout, "
    "dropped connection, or request cancellation. See "
    "https://docs.anthropic.com/en/api/errors#long-requests for more details.",
)
