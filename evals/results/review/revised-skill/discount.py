"""Apply a discount to integer cents. Discount percent must be from 0 to 100."""


def discounted_cents(cents, percent):
    if cents < 0:
        raise ValueError("cents must be nonnegative")
    if percent < 0 and percent > 100:
        raise ValueError("percent must be between 0 and 100")
    return round(cents * (100 - percent) / 100)
