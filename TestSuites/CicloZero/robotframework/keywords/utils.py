import re

def get_ordinal(number: int) -> str:
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    # Handle exceptions to the usual rule for 11th, 12th, and 13th
    if 10 < number % 100 < 14:
        suffix = 'th'
    else:
        suffix = suffixes.get(number % 10, 'th')
    return str(number) + suffix

def get_cardinal(ordinal: str) -> int:
    return int(re.sub(r'[^\d]', '', ordinal))
