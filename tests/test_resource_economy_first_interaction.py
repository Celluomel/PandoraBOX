import inspect

from core.internal_loop import InternalThoughtLoop


def test_internal_loop_eagerly_resolves_resource_economy_before_tick_probes(monkeypatch):
    created = []

    class StubResourceEconomy:
        def __init__(self):
            created.append(self)

    from cognition import cognitive_resource_economy

    monkeypatch.setattr(
        cognitive_resource_economy,
        "CognitiveResourceEconomy",
        StubResourceEconomy,
    )
    loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
    loop._resource_economy = None
    loop._module_tick_log = None

    first = loop._ensure_resource_economy()
    second = loop._ensure_resource_economy()

    assert first is second
    assert created == [first]

    constructor = inspect.getsource(InternalThoughtLoop.__init__)
    assert constructor.index("self._ensure_resource_economy()") < constructor.index(
        "self._refresh_module_tick_probes()"
    )


def test_resource_economy_init_failure_keeps_slow_cycle_retry_available(monkeypatch):
    from cognition import cognitive_resource_economy

    def fail_init():
        raise RuntimeError("unavailable")

    monkeypatch.setattr(
        cognitive_resource_economy,
        "CognitiveResourceEconomy",
        fail_init,
    )
    loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
    loop._resource_economy = None
    loop._module_tick_log = None

    assert loop._ensure_resource_economy() is None
    assert loop._resource_economy is None
