from enum import Enum
import pytest
from state_machine.state_machine import (
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


def test_audit_context_record_transition():
    ctx = AuditContext[State, Event]()
    ctx.record_transition(State.A, Event.X)
    assert ctx._audit == [(State.A, Event.X)]


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
