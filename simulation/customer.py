"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   customer.py
Description :   Sample logic of the customers for the COPROLOOPS simulation

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
"""
import network_nodes


def select_distribution_center(customer, demand, quantity, data):
    """ Selecting distribution center to order from """
    best_route = None
    best_cost = None
    for route in customer.route_ends:
        node = data.network_nodes[route.source]
        if isinstance(node, network_nodes.DistributionCenter) and node.is_valid(data.env.now):
            # Check if enough inventory
            if not demand.is_backlog and node.inventory[demand.material]['quantity'] < quantity:
                continue
            transport_mode = data.transport_modes[route.mode]
            distance = data.get_distance(customer.name, route.source)
            cost = quantity * node.inventory[demand.material]['price']
            # Adding transportation cost if paid by the customer
            if route.costcenter == customer.name:
                cost += transport_mode.fixedcost + transport_mode.distancecost * distance
            if best_route is None or cost < best_cost:
                best_route = route
                best_cost = cost
    return best_route


def select_collection_center(customer, data):
    """ Selecting collection center for return used products """
    best_route = None
    best_cost = None
    for route in customer.route_starts:
        node = data.network_nodes[route.destination]
        if isinstance(node, network_nodes.CollectionCenter) and node.is_valid(data.env.now):
            transport_mode = data.transport_modes[route.mode]
            distance = data.get_distance(customer.name, route.destination)
            cost = transport_mode.fixedcost + transport_mode.distancecost * distance
            if best_route is None or cost < best_cost:
                best_route = route
                best_cost = cost
    return best_route
