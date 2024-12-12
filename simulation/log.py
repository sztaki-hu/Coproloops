"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   log.py
Description :   Class for collecting simulation logs

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
"""

import datetime
from enum import Enum


class LogType(Enum):
    """ Constants for the different log types """
    ORDER = 1
    INVENTORY = 2
    PRODUCTION_START = 3
    PRODUCTION_END = 4
    TRANSPORT_START = 5
    TRANSPORT_END = 6
    INCOME = 7
    RETURN = 8
    DISASSEMBLY_START = 9
    DISASSEMBLY_END = 10
    DISTURBANCE = 11


class Log:
    """ Class for collecting simulation logs """
    logs = []
    properties = []
    starttime = None

    def __init__(self, time, node, node_type, type, quantity, material, node2, mode, cost, costcenter, properties, comment):
        self.time = (self.starttime + datetime.timedelta(time)).date()
        self.node = node
        self.node_type = node_type
        self.type = type
        self.quantity = quantity
        self.material = material
        self.node2 = node2
        self.mode = mode
        self.cost = cost
        self.costcenter = costcenter
        if properties is not None:
            self.properties = properties
        else:
            self.properties = dict()
        self.comment = comment

    @classmethod
    def log(cls, data, node, type, quantity, material, node2, mode, cost, costcenter, properties, comment=None):
        """ Adding a new log entry """
        node_type = data.network_nodes[node].get_type()
        log = Log(data.env.now, node, node_type, type, quantity, material, node2, mode, cost, costcenter, properties, comment)
        cls.logs.append(log)

    @classmethod
    def print_logs(cls):
        props = ''
        for p in cls.properties:
            props += p.ljust(15)
        print ('Date'.ljust(12) + \
            'Node'.ljust(15) + \
            'Node type'.ljust(20) + \
            'Event'.ljust(20) + \
            'Quantity'.ljust(15) + \
            'Material'.ljust(10) + \
            'Node2'.ljust(15) + \
            'Mode'.ljust(10) + \
            'Cost'.ljust(15) + \
            'Cost center'.ljust(15) + \
            props + \
            'Comment')
        for log in cls.logs:
            print(log)

    def __str__(self):
        props = ''
        for p in Log.properties:
            if p in self.properties.keys():
                props += str(round(self.properties[p], 2)).ljust(15)
            else:
                props += ''.ljust(15)
        cost = round(self.cost, 2) if self.cost is not None else ''
        node = self.node[0:15] if self.node is not None else ''
        node2 = self.node2[0:15] if self.node2 is not None else ''
        costcenter = self.costcenter[0:15] if self.costcenter is not None else ''
        return str(self.time).ljust(12) + \
            str(node).ljust(15) + \
            str(self.node_type).ljust(20) + \
            str(self.type.name).ljust(20) + \
            str(self.quantity).ljust(15) + \
            str(self.material).ljust(10) + \
            str(node2).ljust(15) + \
            str(self.mode if self.mode is not None else '').ljust(10) + \
            str(cost).ljust(15) + \
            str(costcenter).ljust(15) + \
            props + \
            str(self.comment if self.comment is not None else '')


    @classmethod
    def get_summary(cls):
        """ Creating summary of KPIs for cost centers """
        summary = dict()
        for log in cls.logs:
            if log.costcenter is not None and (log.cost is not None or log.properties):
                data = None
                if log.costcenter in summary.keys():
                    data = summary[log.costcenter]
                else:
                    data = {'cost': 0, 'income': 0}
                    for p in cls.properties:
                        data[p] = 0
                    summary[log.costcenter] = data
                if log.cost is not None:
                    if log.type != LogType.INCOME:
                        data['cost'] += log.cost
                    else:
                        data['income'] += log.cost
                for p in log.properties.keys():
                    data[p] += log.properties[p]
        return summary


    @classmethod
    def get_logtable(cls):
        """ Creating simulation log table for the dashboard """
        times = []
        nodes = []
        node_types = []
        events = []
        quantities = []
        materials = []
        node2s = []
        modes = []
        costs = []
        cost_centers = []
        properties = dict()
        comments = []
        for p in cls.properties:
            properties[p] = []
        for log in cls.logs:
            cost = None
            if log.cost is not None:
                cost = round(log.cost, 2)
            # times.append(str(floor(log.time)))
            times.append(str(log.time))
            nodes.append(log.node)
            node_types.append(log.node_type)
            events.append(str(log.type.name))
            quantities.append(log.quantity)
            materials.append(log.material)
            node2s.append(log.node2)
            modes.append(log.mode)
            costs.append(cost)
            cost_centers.append(log.costcenter)
            for p in cls.properties:
                if p in log.properties.keys():
                    properties[p].append(round(log.properties[p], 2))
                else:
                    properties[p].append(None)
            comments.append(log.comment)
        result = {'time': times,
                'node': nodes,
                'node_type': node_types,
                'event': events,
                'quantity': quantities,
                'material': materials,
                'node2': node2s,
                'mode': modes,
                'cost': costs,
                'cost_center': cost_centers,
                'comment': comments}
        for p in cls.properties:
            result[p] = properties[p]
        return result

