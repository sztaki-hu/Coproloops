"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   distribution_center.py
Description :   Sample logic of the distribution centers for the COPROLOOPS simulation

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
"""
import network_nodes

# Multipliers for the (s, S) inventory policy (related to the average demand)
s_MULTIPLIER = 2
S_MULTIPLIER = 10


def order_quantity(dc, history, inventory, quantity):
    """ Order up to S if inventory is below s
        'quantity' can be used for lot-for-lot policy
    """
    s, S = getsS(dc, history)
    if inventory >= s:
        return 0
    return S-inventory


def getsS(dc, history):
    """ Sample (s,S) levels for the distribution center
        Average demand multiplied by constants, independently of the distribution center
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
        return 0, 0
    return round(s_MULTIPLIER * sum / (last - first + 1)), round(S_MULTIPLIER * sum / (last - first + 1))


def select_plant(dc, material, quantity, data):
    """ Selecting plant to order from """
    best_route = None
    best_cost = None
    for route in dc.route_ends:
        node = data.network_nodes[route.source]
        if isinstance(node, network_nodes.ProductionSite) and node.is_valid(data.env.now):
            # Check if plant produces material
            if material not in node.produced_materials.keys():
                continue
            transport_mode = data.transport_modes[route.mode]
            distance = data.get_distance(dc.name, route.source)
            cost = quantity * node.inventory[material]['price']
            # Adding transportation cost if paid by the distribution center
            if route.costcenter == dc.name:
                cost += transport_mode.fixedcost + transport_mode.distancecost * distance
            if best_route is None or cost < best_cost:
                best_route = route
                best_cost = cost
    return best_route

