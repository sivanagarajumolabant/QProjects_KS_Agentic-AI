def describe(value):
    match value:
        case 0:
            return "Zero"
        case 1 | 2 | 3:
            return "Small number"
        case _:
            return "Other value"

print(describe(2))  # Output: Small number

def process(value):
    match value:
        case (x, y) if x == y:
            return "Matched tuple with equal elements"
        case [x, y] if x > y:
            return "Matched list with x greater than y"
        case _:
            return "Default case"
print(process((2, 2)))  # Output: Matched tuple with equal elements
