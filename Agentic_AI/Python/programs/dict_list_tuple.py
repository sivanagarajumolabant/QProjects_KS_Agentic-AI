d = {}

#d[[1,2]] = "List"  # raise Typeerror
d[(1,2)] = "Tuple"

print(d) # {(1,2):'Tuple'}