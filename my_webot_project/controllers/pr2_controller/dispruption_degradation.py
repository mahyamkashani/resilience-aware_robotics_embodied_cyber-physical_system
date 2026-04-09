# Def 6: Tolerable disruption
def disruption(S, tau, epsilon, current_task, current_goal):

    for d in S:
        if tau.get((d, current_task), 0) == 2 or epsilon.get((d, current_goal), 0) == 2:
            #print("Critical component in S")
            return 0
    return 1


# Def 7: monotonic degradation function
def monotonic_degradation(S, tau, epsilon, current_task, current_goal):
    value = 1
    for d in S:

        level = max(
            tau.get((d, current_task), 0), 
            epsilon.get((d, current_goal), 0)
        )
        if level == 2:
            value = value - 0.2
        elif level == 1:
            value = value - 0.05
    
    #print(f'Psi value {max(value,0)}')
    return max(value, 0)


# Def 7: Tolerable Degradation
def degradation(S, tau, epsilon, current_task, current_goal):

    psi = monotonic_degradation(S, tau, epsilon, current_task, current_goal)

    for d in S:
        level = max(
            tau.get((d, current_task), 0), 
            epsilon.get((d, current_goal), 0)
        )
        if level == 2:
            theta = 0.85 # theta_crit
        elif level == 1:
            theta = 0.75 # theta_base
        else:
            continue

        if psi < theta:
            return 0
    return 1


