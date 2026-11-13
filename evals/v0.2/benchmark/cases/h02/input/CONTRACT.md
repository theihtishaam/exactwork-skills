# FIFO queue contract
TaskQueue accepts a capacity greater than zero. put adds an item, get removes and
returns the oldest item, and len reports the number currently queued. Any Python
object, including None and false-like values, is a valid item. A full put raises
OverflowError without changing queued items. An empty get raises IndexError.
Separate TaskQueue instances are independent. The module does not claim to be
thread-safe. Input type validation beyond the stated capacity constraint is outside
the review scope. Focus on behavior promised here; do not edit the implementation.
