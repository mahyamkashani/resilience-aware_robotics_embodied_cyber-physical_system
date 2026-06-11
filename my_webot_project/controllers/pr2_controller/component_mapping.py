# Maps low-level robot components to a high-level functional representation.

from constants import COMPONENT_MAP


def map_to_high_level(S_low, component_map):
    S_high  = set()

    for comp, devices in component_map.items():
        if any(d in S_low for d in devices):
            S_high.add(comp)

    return S_high