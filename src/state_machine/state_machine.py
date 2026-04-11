from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, cast

type Action[C] = Callable[[C], None]
"""A callable that performs an action on a context object."""

type Transition[S: Enum, E: Enum, C] = dict[tuple[S, E], tuple[S, Action[C]]]
"""A mapping of (state, event) to (target_state, action)."""


@dataclass
class AuditContext[S: Enum, E: Enum]:
    """A context class that records the history of state transitions.

    Args:
        S: The Enum type representing the states.
        E: The Enum type representing the events.

    Notes:
        Architectural Intent: Provides a standardized mixin for state machine
        contexts that require auditing capabilities. It is designed to be
        inherited by user-defined context classes.
    """

    _audit: list[tuple[S, E]] = field(default_factory=list)

    def record_transition(self, from_state: S, event: E) -> None:
        """Records a transition from a given state triggered by an event.

        Args:
            from_state: The state the machine is transitioning from.
            event: The event that triggered the transition.
        """
        self._audit.append((from_state, event))


class InvalidTransition(Exception):
    """Raised when a transition is not defined for a given state and event."""

    pass


@dataclass
class StateMachine[S: Enum, E: Enum, C]:
    """A lightweight, type-safe state machine.

    The state machine is stateless; the current state must be managed externally
    and passed to the `handle_transition` method.

    Args:
        S: The Enum type representing the states.
        E: The Enum type representing the events.
        C: The type of the context object passed to actions.

    Notes:
        Architectural Intent: Leverages PEP 695 type parameters to ensure
        strict type safety across states, events, and context objects without
        sacrificing flexibility.
    """

    _transitions: Transition[S, E, C] = field(default_factory=dict)

    def add_transition(
        self, from_state: S, event: E, to_state: S, func: Action[C]
    ) -> None:
        """Manually registers a transition between states.

        Args:
            from_state: The starting state for the transition.
            event: The event that triggers the transition.
            to_state: The target state after the transition.
            func: The action to execute during the transition.
        """
        self._transitions[(from_state, event)] = (to_state, func)

    def handle_transition(self, ctx: C, from_state: S, event: E) -> S:
        """Executes a transition and returns the new state.

        Args:
            ctx: The context object to pass to the transition's action.
            from_state: The current state of the machine.
            event: The event to process.

        Returns:
            S: The new state of the machine.

        Raises:
            InvalidTransition: If the transition is not defined for the
                given state and event.
        """
        to_state, action = self._next_transition(from_state, event)
        action(ctx)
        return to_state

    def _next_transition(self, from_state: S, event: E) -> tuple[S, Action[C]]:
        """Internal helper to retrieve the next transition.

        Args:
            from_state: The current state.
            event: The event.

        Returns:
            tuple[S, Action[C]]: A tuple of (target_state, action).

        Raises:
            InvalidTransition: If the transition key is missing.
        """
        try:
            return self._transitions[(from_state, event)]
        except KeyError as e:
            raise InvalidTransition(
                f"Cannot {event.name} when {from_state.name}"
            ) from e

    def transition(
        self, from_state: S | Iterable[S], event: E, to_state: S
    ) -> Callable[[Action[C]], Action[C]]:
        """A decorator to register a transition for a function.

        Args:
            from_state: A single state or an iterable of states that can
                trigger this transition.
            event: The event that triggers the transition.
            to_state: The target state after the transition.

        Returns:
            Callable[[Action[C]], Action[C]]: The decorator function.

        Notes:
            Architectural Intent: Allows for a declarative way to map
            multiple source states to a single target state and action.
        """
        states: list[S]
        if isinstance(from_state, Enum):
            states = [cast(S, from_state)]
        else:
            states = list(cast(Iterable[S], from_state))

        def decorator(func: Action[C]) -> Action[C]:
            for s in states:
                self.add_transition(s, event, to_state, func)
            return func

        return decorator


@dataclass
class AuditedStateMachine[S: Enum, E: Enum, C: AuditContext](StateMachine[S, E, C]):
    """A state machine that automatically records transitions in the context.

    Requires a context that inherits from `AuditContext`.

    Args:
        S: The Enum type representing the states.
        E: The Enum type representing the events.
        C: A context type that implements `AuditContext`.

    Notes:
        Architectural Intent: Simplifies auditing by automatically calling
        `record_transition` on the context before executing the standard
        transition logic.
    """

    def handle_transition(self, ctx: C, from_state: S, event: E) -> S:
        """Records the transition and then executes it.

        Args:
            ctx: The audit context.
            from_state: The current state.
            event: The event to process.

        Returns:
            S: The new state.

        Raises:
            InvalidTransition: If the transition is not defined.
        """
        ctx.record_transition(from_state, event)
        return super().handle_transition(ctx, from_state, event)
