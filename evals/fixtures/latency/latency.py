"""Small synthetic latency utility; durations are nonnegative numbers or None."""


def mean_latency(values):
    present = [value for value in values if value]
    return sum(present) / len(present) if present else None


def maximum_latency(values):
    present = [value for value in values if value is not None]
    return max(present) if present else None
