"""Core decision logic.

This is the heart of Context Lantern. Three lines of business logic,
shared across all hosts. If a new policy is needed (e.g. progressive
warnings), it goes here — never in an Adapter.
"""

from __future__ import annotations

from context_lantern.core.models import (
    Decision,
    MeasureResult,
    ReminderDecision,
)
from context_lantern.core.state import StateStore

DEFAULT_THRESHOLD = 120_000


def format_k(tokens: int) -> str:
    """Format token count as human-readable (e.g. 125000 -> '125k')."""
    return f"{round(tokens / 1000)}k"


def make_decision(
    measure: MeasureResult,
    threshold: int,
    state: StateStore | None,
) -> ReminderDecision:
    """Make a reminder decision based on measurement and state.

    The rule is simple:
        should_warn = (
            input_tokens >= threshold
            AND NOT already_reminded
            AND NOT loop_prevention
        )

    All three conditions must be met for a WARN_ONCE decision.
    """
    input_tokens = measure.snapshot.input_tokens
    already_reminded = (
        state.is_reminded(measure.dedup_key, threshold)
        if state is not None
        else False
    )

    below_threshold = input_tokens < threshold
    if below_threshold:
        return ReminderDecision(
            decision=Decision.SILENT,
            snapshot=measure.snapshot,
            threshold=threshold,
            already_reminded=already_reminded,
        )

    if already_reminded:
        return ReminderDecision(
            decision=Decision.SILENT,
            snapshot=measure.snapshot,
            threshold=threshold,
            already_reminded=True,
        )

    if measure.loop_prevention:
        return ReminderDecision(
            decision=Decision.SILENT,
            snapshot=measure.snapshot,
            threshold=threshold,
            message="suppressed: host loop prevention active",
        )

    # Threshold crossed, not yet reminded, no loop prevention -> warn.
    message = (
        f"Session input ~{format_k(input_tokens)}, "
        f"threshold {format_k(threshold)}."
    )

    # Record the reminder in state.
    if state is not None:
        state.mark_reminded(
            key=measure.dedup_key,
            input_tokens=input_tokens,
            threshold=threshold,
            source=measure.snapshot.source,
        )

    return ReminderDecision(
        decision=Decision.WARN_ONCE,
        snapshot=measure.snapshot,
        threshold=threshold,
        message=message,
        already_reminded=False,
    )
