from enum import Enum
import pytest
from semantic_state_machine.state_machine import (
    AuditContext,
    AuditedStateMachine,
    InvalidTransition,
    StateMachine,
)


class State(Enum):
    A = 1
    B = 2
    C = 3


class Event(Enum):
    X = 1
    Y = 2


class MyContext(AuditContext[State, Event]):
    def __init__(self):
        super().__init__()
        self.action_called = False

    def mark_called(self):
        self.action_called = True


def test_audit_context_formatter_coverage():
    ctx = AuditContext[State, Event]()
    ctx.record_transition(State.A, Event.X)
    ctx.record_transition(State.B, Event.Y)

    # Test custom formatter (counting transitions - covers line 90)
    count = ctx.audit_trail(lambda trail: len(trail))
    assert count == 2

    # Test no formatter (covers line 91)
    trail = ctx.audit_trail()
    assert trail == [(State.A, Event.X), (State.B, Event.Y)]


def test_state_machine_transitions_property():
    sm = StateMachine[State, Event, MyContext]()

    def action1(ctx: MyContext):
        pass

    def action2(ctx: MyContext):
        pass

    sm.add_transition(State.A, Event.X, State.B, action1)
    sm.add_transition(State.B, Event.Y, State.C, action2)

    transitions = sm.transitions
    assert len(transitions) == 2
    # Check that keys and values exist
    assert any(k == (State.A, Event.X) and v[0] == State.B for k, v in transitions)
    assert any(k == (State.B, Event.Y) and v[0] == State.C for k, v in transitions)


def test_state_machine_transition_decorator_iterable_states():
    sm = StateMachine[State, Event, MyContext]()

    @sm.transition([State.A, State.B], Event.X, State.C)
    def my_action(ctx: MyContext) -> None:
        ctx.mark_called()

    ctx = MyContext()

    # Test transition from State A
    sm.handle_transition(ctx, State.A, Event.X)
    assert ctx.action_called is True

    # Reset and test from State B
    ctx.action_called = False
    sm.handle_transition(ctx, State.B, Event.X)
    assert ctx.action_called is True


def test_audited_state_machine_records_multiple_states():
    sm = AuditedStateMachine[State, Event, MyContext]()

    @sm.transition([State.A, State.B], Event.X, State.A)
    def my_action(ctx: MyContext):
        pass

    ctx = MyContext()
    sm.handle_transition(ctx, State.A, Event.X)
    sm.handle_transition(ctx, State.B, Event.X)

    assert ctx._audit == [(State.A, Event.X), (State.B, Event.X)]


def test_audited_state_machine_records_transition():
    sm = AuditedStateMachine[State, Event, MyContext]()

    @sm.transition(State.A, Event.X, State.B)
    def my_action(ctx: MyContext):
        pass

    ctx = MyContext()
    new_state = sm.handle_transition(ctx, State.A, Event.X)

    assert new_state == State.B
    assert (State.A, Event.X) in ctx._audit


def test_state_machine_add_transition_direct():
    sm = StateMachine[State, Event, MyContext]()

    def my_action(ctx: MyContext):
        ctx.mark_called()

    sm.add_transition(State.A, Event.X, State.B, my_action)

    ctx = MyContext()
    new_state = sm.handle_transition(ctx, State.A, Event.X)

    assert new_state == State.B
    assert ctx.action_called is True


def test_state_machine_handle_transition_invalid():
    sm = StateMachine[State, Event, MyContext]()
    ctx = MyContext()

    with pytest.raises(InvalidTransition, match="Cannot X when A"):
        sm.handle_transition(ctx, State.A, Event.X)


def test_state_machine_transition_decorator_single_state():
    sm = StateMachine[State, Event, MyContext]()

    @sm.transition(State.A, Event.Y, State.C)
    def my_action(ctx: MyContext):
        ctx.mark_called()

    ctx = MyContext()
    new_state = sm.handle_transition(ctx, State.A, Event.Y)

    assert new_state == State.C
    assert ctx.action_called is True
