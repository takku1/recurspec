from dataclasses import dataclass

import pytest

from recurspec.spec_runner.runtime import (
    MessagesResult,
    RuntimeAdapterError,
    anthropic_messages_client,
    messages_runtime,
)
from recurspec.spec_runner.workers import WorkerPool


@dataclass(frozen=True)
class Packet:
    contract_card: str
    own_draft: str


def test_messages_runtime_sends_only_serialized_packet_never_a_path():
    seen: dict[str, str] = {}

    def client(system: str, user: str, model: str) -> MessagesResult:
        seen.update(system=system, user=user, model=model)
        return MessagesResult('{"approved": true}', 3, 2)

    runtime = messages_runtime(client, cheap_model="cheap-model", capable_model="capable-model")
    response = runtime(Packet("card", "draft"), "check", "cheap")

    assert response.body == {"approved": True}
    assert response.tokens_in == 3
    assert response.tokens_out == 2
    assert seen["model"] == "cheap-model"
    assert "card" in seen["user"]
    assert "tree_root" not in seen["user"]
    assert "own_draft" in seen["user"]


def test_messages_runtime_routes_capable_tier_to_the_capable_model():
    models: list[str] = []

    def client(_system: str, _user: str, model: str) -> MessagesResult:
        models.append(model)
        return MessagesResult("{}", 1, 1)

    runtime = messages_runtime(client, cheap_model="haiku", capable_model="opus")
    runtime({"x": 1}, "resolve", "capable")

    assert models == ["opus"]


def test_messages_runtime_refuses_a_non_json_body():
    runtime = messages_runtime(
        lambda *_a: MessagesResult("not json at all", 1, 1),
        cheap_model="c",
        capable_model="k",
    )

    with pytest.raises(RuntimeAdapterError, match="not a JSON object"):
        runtime({}, "frame", "cheap")


def test_pool_records_tool_error_when_the_adapter_rejects_prose():
    runtime = messages_runtime(
        lambda *_a: MessagesResult("sorry, here is prose", 4, 4),
        cheap_model="c",
        capable_model="k",
    )
    pool = WorkerPool(runtime, concurrency=1)

    result = pool.dispatch("node-1", {"packet": True}, "frame", "maker", 100)

    assert result.outcome == "tool_error"
    assert result.body is None


def test_anthropic_client_factory_explains_a_missing_extra(monkeypatch: pytest.MonkeyPatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "anthropic":
            raise ImportError("missing")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match=r"recurspec\[runtime\]"):
        anthropic_messages_client()
