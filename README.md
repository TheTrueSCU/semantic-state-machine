# State Machine

A lightweight, type-safe Python state machine implementation using modern Python 3.13+ features like PEP 695 type parameters.

## Features

- **Type Safety**: Leverage Python's type system to ensure consistent states, events, and contexts.
- **Decorator Support**: Easily define transitions using the `@sm.transition` decorator.
- **Auditing**: Built-in support for recording transition history via `AuditedStateMachine` and `AuditContext`.
- **Flexible Context**: Pass a custom context object to transition actions to maintain state outside the machine.

## Installation

This project uses `uv` for dependency management. To get started, ensure you have `uv` installed and run:

```bash
uv sync
```

You can install the package via pip:

```bash
pip install semantic-state-machine
```

## Usage

### Basic State Machine

Define your states and events as `Enum`s and create a context class.

```python
from enum import Enum
from semantic_state_machine import StateMachine

class State(Enum):
    LOCKED = 1
    UNLOCKED = 2

class Event(Enum):
    PUSH = 1
    COIN = 2

class TurnstileContext:
    def __init__(self):
        self.total_coins = 0

sm = StateMachine[State, Event, TurnstileContext]()

@sm.transition(State.LOCKED, Event.COIN, State.UNLOCKED)
def insert_coin(ctx: TurnstileContext):
    ctx.total_coins += 1
    print("Coin inserted. Turnstile unlocked.")

@sm.transition(State.UNLOCKED, Event.PUSH, State.LOCKED)
def push_turnstile(ctx: TurnstileContext):
    print("Turnstile pushed. Turnstile locked.")

# Usage
ctx = TurnstileContext()
current_state = State.LOCKED
current_state = sm.handle_transition(ctx, current_state, Event.COIN)
# current_state is now State.UNLOCKED
```

### Audited State Machine

Use `AuditedStateMachine` and `AuditContext` to automatically track the history of transitions.

```python
from semantic_state_machine import AuditedStateMachine, AuditContext

class MyContext(AuditContext[State, Event]):
    pass

sm = AuditedStateMachine[State, Event, MyContext]()

# Transitions are defined the same way
@sm.transition(State.LOCKED, Event.COIN, State.UNLOCKED)
def insert_coin(ctx: MyContext):
    pass

ctx = MyContext()
sm.handle_transition(ctx, State.LOCKED, Event.COIN)

# The transition is automatically recorded
print(ctx._audit)  # [(State.LOCKED, Event.COIN)]
```

## Testing

The project includes a comprehensive suite of unit and integration tests.

### Run All Tests
```bash
uv run pytest tests/
```

### Run with Coverage
```bash
uv run pytest --cov=src tests/
```

The current implementation maintains **100% code coverage** across the core logic and integration workflows.

## Project Structure

- `src/semantic_state_machine/`: Core implementation.
- `tests/unit/`: Focused unit tests for individual components.
- `tests/integration/`: End-to-end workflow simulations.
