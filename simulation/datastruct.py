"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   datastruct.py
Description :   Database interface and data structure for the COPROLOOPS simulation

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
"""

from math import radians, cos, sin, asin, sqrt
import sqlite3
import datetime
import random
from log import Log
import distribution
from network_nodes import (NetworkNode, Customer, DistributionCenter, ProductionSite, CollectionCenter,
                           RecoveryPlant)

class DataStructure:
    """ Class for reading and storing master data """
    def __init__(self, database, starttime, env):
        self.starttime = starttime
        self.env = env
        self.cost_centers = dict()
        self.distributions = dict()
        self.disturbances = dict()
        self.network_nodes = dict()
        self.materials = dict()
        self.transport_modes = dict()
        self.node_distances = dict()
        self.read_all(database)

    def read_all(self, database):
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        self.read_cost_centers(cursor)
        self.read_distributions(cursor)
        self.read_disturbances(cursor)
        operation_properties = self.read_operation_property_classes(cursor)
        self.read_transport_modes(cursor, operation_properties)
        self.read_network_nodes(cursor, operation_properties)
        self.read_inventories(cursor)
        self.read_demands(cursor)
        self.read_materials(cursor)
        self.read_routes(cursor)
        self.read_produced_materials(cursor, operation_properties)
        self.read_disassembled_materials(cursor, operation_properties)
        conn.close()

    def read_cost_centers(self, cursor):
        cursor.execute('SELECT * FROM CostCenter')
        for name in cursor.fetchall():
            self.cost_centers[name] = CostCenter(name)

    def read_distributions(self, cursor):
        cursor.execute('SELECT * FROM Distribution')
        for id, type, min, max, avg, std in cursor.fetchall():
            self.distributions[id] = Distribution(type, min, max, avg, std)

    def read_disturbances(self, cursor):
        cursor.execute('SELECT * FROM Disturbance')
        for id, pobability, duration, loss in cursor.fetchall():
            self.disturbances[id] = Disturbance(pobability, self.distributions[duration], loss)

    def read_operation_property_classes(self, cursor):
        cursor.execute('SELECT * FROM OperationProperty')
        for property, in cursor.fetchall():
            Log.properties.append(property)
        properties = dict()
        cursor.execute('SELECT * FROM OperationPropertyLink')
        for id, property, value in cursor.fetchall():
            property_list = None
            if id in properties.keys():
                property_list = properties[id]
            else:
                property_list = []
                properties[id] = property_list
            property_list.append({'property': property, 'value': value})
        return properties

    # def get_operation_properties(self, properties, id):
    #     if id not in properties.keys():
    #         raise Exception('Cannot find operation properties %s' % id)
    #     return properties[id]

    def read_transport_modes(self, cursor, properties):
        cursor.execute('SELECT * FROM TransportMode')
        for name, fixedcost, distancecost, time, disturbanceid, property_id in cursor.fetchall():
            disturbance = None
            if disturbanceid is not None:
                disturbance = self.disturbances[disturbanceid]
            self.transport_modes[name] = TransportMode(name, fixedcost, distancecost, time, disturbance, properties[property_id])

    def read_network_nodes(self, cursor, properties):
        cursor.execute('SELECT * FROM NetworkNode')
        for name, latitude, longitude, costcenter, disturbanceid in cursor.fetchall():
            disturbance = None
            if disturbanceid is not None:
                disturbance = self.disturbances[disturbanceid]
            self.network_nodes[name] = NetworkNode(name, latitude, longitude, costcenter, disturbance)
        cursor.execute('SELECT * FROM ProductionSite')
        for name, capacity in cursor.fetchall():
            self.network_nodes[name] = ProductionSite(self.network_nodes[name], capacity)
        cursor.execute('SELECT * FROM DistributionCenter')
        for name, capacity, property_id in cursor.fetchall():
            property = None
            if property_id is not None:
                property = properties[property_id]
            self.network_nodes[name] = DistributionCenter(self.network_nodes[name], capacity, property)
        cursor.execute('SELECT * FROM Customer')
        for name, in cursor.fetchall():
            self.network_nodes[name] = Customer(self.network_nodes[name])
        cursor.execute('SELECT * FROM CollectionCenter')
        for name, capacity, property_id in cursor.fetchall():
            property = None
            if property_id is not None:
                property = properties[property_id]
            self.network_nodes[name] = CollectionCenter(self.network_nodes[name], capacity, property)
        cursor.execute('SELECT * FROM RecoveryPlant')
        for name, capacity in cursor.fetchall():
            self.network_nodes[name] = RecoveryPlant(self.network_nodes[name], capacity)
        cursor.execute('SELECT * FROM Validity')
        for name, start, end in cursor.fetchall():
            if None != start:
                start = (datetime.datetime.fromisoformat(start)-self.starttime).days
            if None != end:
                end = (datetime.datetime.fromisoformat(end)-self.starttime).days
            self.network_nodes[name].validity.append({'start': start, 'end': end})

    def read_inventories(self, cursor):
        cursor.execute('SELECT * FROM Inventory')
        for material, node, quantity, price in cursor.fetchall():
            self.network_nodes[node].set_inventory(material, quantity, price)

    def read_demands(self, cursor):
        cursor.execute('SELECT * FROM Demand')
        for customer, material, frequency, quantity_distribution, is_backlog, additional_trend, multiplicative_trend, duedate, waste_production in cursor.fetchall():
            self.network_nodes[customer].demand[material] = Demand(material, frequency, self.distributions[quantity_distribution], is_backlog,
                                                      additional_trend, multiplicative_trend, duedate, waste_production)

    def read_materials(self, cursor):
        cursor.execute('SELECT * FROM Material')
        for name, volume, mass in cursor.fetchall():
            self.materials[name] = Material(name, volume, mass)
        cursor.execute('SELECT * FROM BOM')
        for product, component, quantity in cursor.fetchall():
            self.materials[product].add_bom(component, quantity)
        # cursor.execute('SELECT link.MaterialName, prop.Name FROM MaterialPropertyLink link ' +
        #                'JOIN MaterialProperty prop ON link.MaterialPropertyName = prop.Name ')
        cursor.execute('SELECT * FROM MaterialPropertyLink')
        for material, property, value in cursor.fetchall():
            self.materials[material].properties.append({'property': property, 'value': value})

    def read_routes(self, cursor):
        cursor.execute('SELECT * FROM Route')
        for source, destination, mode, costcenter in cursor.fetchall():
            route = Route(source, destination, mode, costcenter)
            self.network_nodes[source].route_starts.append(route)
            self.network_nodes[destination].route_ends.append(route)

    def read_produced_materials(self, cursor, properties):
        cursor.execute('SELECT * FROM ProducedMaterial')
        for node, material, cost, time, capacity_usage, price, property_id in cursor.fetchall():
            self.network_nodes[node].produced_materials[material] = ProducedMaterial(cost, time, capacity_usage, price, properties[property_id])

    def read_disassembled_materials(self, cursor, properties):
        cursor.execute('SELECT * FROM DisassembledMaterial')
        for product, node, cost, time, capacity_usage, property_id in cursor.fetchall():
            self.network_nodes[node].disassembled_materials[product] = DisassembledMaterial(cost, time, capacity_usage, properties[property_id])
        cursor.execute('SELECT * FROM InverseBOM')
        for product, node, component, quantity, price in cursor.fetchall():
            self.network_nodes[node].disassembled_materials[product].inverse_bom[component] = InverseBOM(self.distributions[quantity], price)

    def calculate_distance(self, node1, node2):
        """ Computes distance between two nodes """
        lon1 = radians(self.network_nodes[node1].longitude)
        lon2 = radians(self.network_nodes[node2].longitude)
        lat1 = radians(self.network_nodes[node1].latitude)
        lat2 = radians(self.network_nodes[node2].latitude)
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        # 6371 is the radius of earth in kilometers
        return c * 6371

    def get_distance(self, node1, node2):
        """ Returns distance between two nodes -- computes distances maximum one time """
        distances = None
        if node1 in self.node_distances:
            distances = self.node_distances[node1]
        else:
            distances = dict()
            self.node_distances[node1] = distances
        if node2 in distances:
            return distances[node2]
        d = self.calculate_distance(node1, node2)
        distances[node2] = d
        return d

class CostCenter:
    def __init__(self, name):
        self.name = name


class Distribution:
    def __init__(self, type, min, max, avg, std):
        self.type = type
        self.min = min
        self.max = max
        self.avg = avg
        self.std = std


class Disturbance:
    def __init__(self, probability, duration, loss):
        self.probability = probability
        self.duration = duration
        self.loss = loss


class Demand:
    def __init__(self, material, frequency, quantity_distribution, is_backlog, additional_trend, multiplicative_trend, duedate, waste_production):
        self.material = material
        self.frequency = frequency
        self.quantity_distribution = quantity_distribution
        self.is_backlog = is_backlog
        self.additional_trend = additional_trend
        self.multiplicative_trend = multiplicative_trend
        self.duedate = duedate
        self.waste_production = waste_production


class Material:
    def __init__(self, name, volume, mass):
        self.name = name
        self.volume = volume
        self.mass = mass
        self.bom = dict()
        self.properties = []

    def add_bom(self, component, quantity):
        self.bom[component] = quantity


class TransportMode:
    def __init__(self, name, fixedcost, distancecost, time, disturbance, properties):
        self.name = name
        self.fixedcost = fixedcost
        self.distancecost = distancecost
        self.time = time
        self.disturbance = disturbance
        self.properties = properties

    def get_disturbance(self, isloss):
        duration = 0
        loss = 0
        if self.disturbance is not None and random.random() < self.disturbance.probability:
            duration = distribution.random_from_distribution(self.disturbance.duration)
            if isloss:
                loss = self.disturbance.loss
        return duration, loss


class Route:
    def __init__(self, source, destination, mode, costcenter):
        self.source = source
        self.destination = destination
        self.mode = mode
        self.costcenter = costcenter


class ProducedMaterial:
    def __init__(self, cost, time, capacity_usage, price, properties):
        self.cost = cost
        self.time = time
        self.capacity_usage = capacity_usage
        self.price = price
        self.properties = properties


class InverseBOM:
    def __init__(self, quantity_distribution, price):
        self.quantity_distribution = quantity_distribution
        self.price = price


class DisassembledMaterial:
    def __init__(self, cost, time, capacity_usage, properties):
        self.cost = cost
        self.time = time
        self.capacity_usage = capacity_usage
        self.inverse_bom = dict()
        self.properties = properties

