"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   collection_center.py
Description :   Sample decision logic of collection centers for the COPROLOOPS simulation

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
"""
import network_nodes

# Multipliers for the inventory policy (related to the average demand)
S_MULTIPLIER = 10


def return_quantity(cc, history, inventory):
    """ Transporting all materials in the inventory if it is above the target level """
    S = getS(cc, history)
    if inventory < S:
        return 0
    return inventory


def getS(cc, history):
    """ Sample target level for the collection center
        Average demand multiplied by a constant, independently of the collection center
    """
    sum = 0
    first = None
    last = None
    for demand in history:
        time = demand['time']
        quantity = demand['quantity']
        sum += quantity
        if first is None or time < first:
            first = time
        if last is None or time > last:
            last = time
    if first is None or last is None:
        return 0
    return round(S_MULTIPLIER * sum / (last - first + 1))


def select_plant(cc, material, data):
    """ Selecting recovery plant """
    best_route = None
    best_cost = None
    for route in cc.route_starts:
        node = data.network_nodes[route.destination]
        if isinstance(node, network_nodes.RecoveryPlant) and material in node.disassembled_materials.keys() and node.is_valid(data.env.now):
            transport_mode = data.transport_modes[route.mode]
            distance = data.get_distance(cc.name, route.destination)
            cost = transport_mode.fixedcost + transport_mode.distancecost * distance
            if best_route is None or cost < best_cost:
                best_route = route
                best_cost = cost
    return best_route
