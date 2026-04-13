import pytest
from enum import Enum, auto
from dataclasses import dataclass
from hypothesis import given, strategies as st
from semantic_state_machine.state_machine import (
    AuditedStateMachine,
    AuditContext,
    InvalidTransition,
)


# 1. Define sample Enums for testing
class State(Enum):
    IDLE = auto()
    RUNNING = auto()
    ERROR = auto()


class Event(Enum):
    START = auto()
    STOP = auto()
    FAIL = auto()


@dataclass
class MyContext(AuditContext[State, Event]):
    data: int = 0


# 2. Setup the state machine
sm = AuditedStateMachine[State, Event, MyContext]()


@sm.transition(from_state=State.IDLE, event=Event.START, to_state=State.RUNNING)
def start_action(ctx: MyContext) -> None:
    ctx.data = 1


@sm.transition(from_state=State.RUNNING, event=Event.STOP, to_state=State.IDLE)
def stop_action(ctx: MyContext) -> None:
    ctx.data = 0


# 3. Hypothesis Strategies
# Generate a sequence of events that follow the valid path IDLE -> RUNNING -> IDLE
valid_transitions = [
    (State.IDLE, Event.START, State.RUNNING),
    (State.RUNNING, Event.STOP, State.IDLE),
]


@given(st.lists(st.sampled_from(valid_transitions), min_size=1, max_size=50))
def test_audit_trail_consistency(transition_sequence):
    ctx = MyContext()
    current_state = State.IDLE

    # Track expected sequence
    expected_audit = []

    for from_state, event, to_state in transition_sequence:
        # Only perform transition if state matches (simple validation for fuzzer)
        if current_state == from_state:
            current_state = sm.handle_transition(ctx, from_state, event)
            expected_audit.append((from_state, event))

    # Verify audit trail
    actual_audit = ctx.audit_trail()
    assert actual_audit == expected_audit
    assert len(actual_audit) == len(expected_audit)


@given(st.sampled_from(list(State)), st.sampled_from(list(Event)))
def test_invalid_transitions(state, event):
    # Skip valid transitions defined above
    if (state == State.IDLE and event == Event.START) or (
        state == State.RUNNING and event == Event.STOP
    ):
        return

    ctx = MyContext()
    with pytest.raises(InvalidTransition):
        sm.handle_transition(ctx, state, event)
