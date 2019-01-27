import math

# thx to washy for to_limit func
def to_limit(args):
    a0, arest = args[0], args[1:]  # separate list in first element and rest
    if len(args) <= 1:
        # end of recursion, we have only the last element left
        return [[i] for i in range(a0)]
    # we get a list here... so we just have to copy the list once, per i until limit
    lst = to_limit(arest)
    return [[i]+l for l in lst for i in range(a0)]

def find_maximum_values(goal, constants):
    output = [0] * len(constants)
    for i in range(len(constants)):
        j = 0
        plausible = True
        while plausible:
            for k in range(len(goal)):
                if j * constants[i][k] > goal[k]:
                    plausible = False
                    break
            if plausible:
                output[i] = j + 1
            j += 1
    return output

def optimal_combination(goal, constants):
    maximum_coeff_values = find_maximum_values(goal, constants)
    permutations = to_limit(maximum_coeff_values)
    
    best_sum = 0
    best_coeffs = []
    for coeffs in permutations:
        total = 0
        for i in range(len(goal)):
            sum = 0
            for j in range(len(coeffs)):
                sum += coeffs[j] * constants[j][i]
            if sum > goal[i]:
                sum = -math.inf
            total += sum
        if total > best_sum:
            best_sum = total
            best_coeffs = coeffs
    return best_coeffs
