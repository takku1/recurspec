"""Packet-only Messages-API adapter for ``WorkerPool``'s ``RuntimeCall``.

This module does not open files, does not take a tree root, and does not
register tools. Claude Agent SDK was surveyed and rejected because it exposes
Read/Write/Bash by default (see docs/research/r-204-runtime-survey.md).
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from .workers import RuntimeCall, RuntimeResponse

MessagesClient = Callable[[str, str, str], "MessagesResult"]


@dataclass(frozen=True)
class MessagesResult:
    text: str
    tokens_in: int
    tokens_out: int


class RuntimeAdapterError(ValueError):
    """The Messages turn completed but could not be turned into a WorkerResult body."""


def _packet_text(packet: Any) -> str:
    if is_dataclass(packet) and not isinstance(packet, type):
        payload: Any = asdict(packet)
    else:
        payload = packet
    return json.dumps(payload, default=str, sort_keys=True)


def _extract_json_object(text: str) -> Any:
    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if match is None:
            raise RuntimeAdapterError("runtime response is not a JSON object") from None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise RuntimeAdapterError("runtime response is not a JSON object") from exc
    if not isinstance(parsed, dict):
        raise RuntimeAdapterError("runtime response is not a JSON object")
    return parsed


def _system_for_phase(phase: str) -> str:
    return (
        "You are a Recurspec worker. Use only the packet. Do not claim to read files "
        f"or the Contract Tree. Phase: {phase}. Reply with one JSON object and nothing else."
    )


def messages_runtime(
    client: MessagesClient,
    *,
    cheap_model: str,
    capable_model: str,
) -> RuntimeCall:
    """Adapt a Messages-shaped client to ``RuntimeCall``.

    ``client`` is (system, user, model) -> MessagesResult. The adapter never
    forwards a path. A non-object body raises ``RuntimeAdapterError`` so the
    pool records ``tool_error`` rather than treating prose as a completed node.
    """

    def call(packet: Any, phase: str, tier: str) -> RuntimeResponse:
        model = cheap_model if tier == "cheap" else capable_model
        started = time.perf_counter()
        result = client(_system_for_phase(phase), _packet_text(packet), model)
        ms = (time.perf_counter() - started) * 1000
        body = _extract_json_object(result.text)
        return RuntimeResponse(body, result.tokens_in, result.tokens_out, ms)

    return call


def anthropic_messages_client() -> MessagesClient:
    """Build a client from the optional ``anthropic`` extra.

    Pin: ``anthropic==0.122.0`` (PyPI, 2026-08-13). Import is deferred so the
    core package stays installable without the extra.
    """
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError(
            "optional runtime extra is not installed: pip install 'recurspec[runtime]'"
        ) from exc

    sdk = Anthropic()

    def client(system: str, user: str, model: str) -> MessagesResult:
        message = sdk.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        usage = message.usage
        tokens_in = getattr(usage, "input_tokens", None)
        tokens_out = getattr(usage, "output_tokens", None)
        if not isinstance(tokens_in, int) or not isinstance(tokens_out, int):
            raise RuntimeAdapterError("Messages API response lacks integer token usage")
        return MessagesResult(text, tokens_in, tokens_out)

    return client
