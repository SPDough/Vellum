"""
Minimal Prefect flow for canonical stack smoke checks.

Run locally:
    python -m flows.canonical_probe
"""

from prefect import flow, task


@task
def probe_message() -> str:
    return "canonical-stack-probe-ok"


@flow(name="canonical-stack-probe")
def canonical_stack_probe() -> str:
    """Smoke flow; lightweight check for Prefect runtime wiring."""
    return probe_message()


if __name__ == "__main__":
    print(canonical_stack_probe())

