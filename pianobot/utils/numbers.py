from math import floor, log10

def display_short(num: float) -> str:
    return display(num, ['', ' k', ' M', ' B', ' T'])

def display_full(num: float) -> str:
    return display(num, ['', ' Thousand', ' Million', ' Billion', ' Trillion'])

def display(num: float, names: list[str]) -> str:
    if num < 10000:
        return str(num)
    pos = max(0, min(len(names) - 1, int(floor(0 if num == 0 else log10(abs(num)) / 3))))
    return f'{round(num / 10 ** (3 * pos), 2):g}{names[pos]}'
