"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   network_nodes.py
Description :   Behavior of the network nodes for the COPROLOOPS simulation

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
02/09/2025      Egri            First public version
"""

import random
import collection_center
import distribution
import distribution_center
import production_site
import customer
import recovery_plant
from log import Log, LogType

# For debugging
PRINT_EVENT_TIMES = False

class Order:
    def __init__(self, customer, material, quantity, route):
        self.customer = customer
        self.material = material
        self.quantity = quantity
        self.route = route


def get_transportation_time(unit_time, distance):
    """ Computing transportation time """
    # TODO: correct transportation time calculation
    if unit_time < 1:
        unit_time *= distance / 100
    return unit_time


class NetworkNode:
    """ Parent class for network nodes with common attributes and methods """
    def __init__(self, name, latitude, longitude, costcenter, disturbance):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.costcenter = costcenter
        self.disturbance = disturbance
        self.inventory = dict()
        self.route_starts = []
        self.route_ends = []
        self.validity = []
        self.demand_history = dict()
        self.open_customer_orders = []
        self.inventory_position_correction = dict()

    def set_inventory(self, material, quantity, price):
        self.inventory[material] = {'quantity': quantity, 'price': price}

    def change_inventory(self, material, quantity, data):
        self.inventory[material]['quantity'] += quantity
        Log.log(data, self.name, LogType.INVENTORY, quantity, material, None, None, None, None, None, comment='New level: %s' % self.inventory[material]['quantity'])

    def get_type(self):
        if isinstance(self, ProductionSite):
            return 'Production site'
        if isinstance(self, DistributionCenter):
            return 'Distribution center'
        if isinstance(self, Customer):
            return 'Customer'
        if isinstance(self, CollectionCenter):
            return 'Collection center'
        if isinstance(self, RecoveryPlant):
            return 'Recovery plant'
        return 'Network node'

    def is_valid(self, now):
        if len(self.validity) == 0:
            return True
        for v in self.validity:
            if v['start'] is not None and v['end'] is not None:
                if v['start'] <= now <= v['end']:
                    return True
            elif v['start'] is not None:
                if v['start'] <= now:
                    return True
            elif v['end'] is not None:
                if now <= v['end']:
                    return True
        return False

    def add_demand_history(self, material, quantity, now):
        if material not in self.demand_history.keys():
            self.demand_history[material] = [{'time': now, 'quantity': quantity}]
        else:
            self.demand_history[material].append({'time': now, 'quantity': quantity})

    def get_disturbance(self):
        duration = 0
        loss = 0
        if self.disturbance is not None and random.random() < self.disturbance.probability:
            duration = distribution.random_from_distribution(self.disturbance.duration)
            loss = self.disturbance.loss
        return duration, loss

    def correct_inventory_position(self, material, quantity):
        if material in self.inventory_position_correction.keys():
            self.inventory_position_correction[material] += quantity
        else:
            self.inventory_position_correction[material] = quantity

    def get_inventory_position(self, material):
        inventory = self.inventory[material]['quantity']
        if material in self.inventory_position_correction.keys():
            inventory += self.inventory_position_correction[material]
        return inventory

    def delivery(self, order, data, isloss):
        """ Satisfying an order
            isloss: loss is allowed in case of a disturbance
            If delivery fulfils and order, loss may result in missing products and stop in production
        """
        # TODO: instead of isloss, generate new order for lost materials
        distance = data.get_distance(self.name, order.customer.name)
        mode_name = None
        cost_center = None
        time = 0
        cost = 0
        duration = 0
        loss = 0
        properties = dict()
        if order.route is not None:
            transport_mode = data.transport_modes[order.route.mode]
            mode_name = transport_mode.name
            cost_center = order.route.costcenter
            time = transport_mode.time
            cost = transport_mode.fixedcost + transport_mode.distancecost * distance
            for property in transport_mode.properties:
                properties[property['property']] = property['value'] * distance
            duration, loss = transport_mode.get_disturbance(isloss)
        time = get_transportation_time(time, distance)
        Log.log(data, self.name, LogType.TRANSPORT_START, order.quantity, order.material, order.customer.name, mode_name, None, None, None, None)
        if duration > 0:
            Log.log(data, self.name, LogType.DISTURBANCE, round(order.quantity * loss), order.material, None, None, None, None, None, 'Transportation')
        else:
            duration = 0
        yield data.env.timeout(time + duration)
        order.quantity *= round(1 - loss)
        Log.log(data, self.name, LogType.TRANSPORT_END, order.quantity, order.material, order.customer.name, mode_name, cost, cost_center, properties, None)
        order.customer.shipment_receive(order.material, order.quantity, data)

    def shipment_receive(self, material, quantity, data):
        pass


class ProductionSite(NetworkNode):
    """ Production sites produces materials (products, components, raw materials) """
    def __init__(self, nn, capacity):
        self.name = nn.name
        self.latitude = nn.latitude
        self.longitude = nn.longitude
        self.costcenter = nn.costcenter
        self.disturbance = nn.disturbance
        self.inventory = nn.inventory
        self.route_starts = nn.route_starts
        self.route_ends = nn.route_ends
        self.validity = nn.validity
        self.demand_history = nn.demand_history
        self.inventory_position_correction = nn.inventory_position_correction
        self.open_customer_orders = nn.open_customer_orders
        self.capacity = capacity
        self.produced_materials = dict()
        self.open_production_orders = []

    def order_management(self, order, data):
        """ Handling incoming order from distribution centers """
        # TODO: order management without history in order to replace loss of a disturbance
        self.add_demand_history(order.material, order.quantity, data.env.now)
        price = self.inventory[order.material]['price'] * order.quantity
        Log.log(data, self.name, LogType.INCOME, order.quantity, order.material, order.customer.name, None, price, self.costcenter, None, None)
        # Can deliver instantly only if both the on-hand inventory and the inventory position is enough
        if self.inventory[order.material]['quantity'] >= order.quantity and self.get_inventory_position(order.material) >= order.quantity:
            self.change_inventory(order.material, -order.quantity, data)
            data.env.process(self.delivery(order, data, False))
        else:
            self.correct_inventory_position(order.material, -order.quantity)
            if order.material in self.produced_materials.keys():
                self.open_customer_orders.append(order)
            else:
                raise Exception("Order for a non-produced material")
        self.inventory_management(order.material, data, order.quantity)

    def inventory_management(self, material, data, order_quantity):
        """ Controlling production and replenishment """
        production_quantity = production_site.production_quantity(self, self.demand_history[material], self.get_inventory_position(material), order_quantity)
        if production_quantity > 0:
            canproduce = True
            # Checking availability of necessary components
            for component in data.materials[material].bom.keys():
                component_quantity = data.materials[material].bom[component] * production_quantity
                self.add_demand_history(component, component_quantity, data.env.now)
                self.correct_inventory_position(component, -component_quantity)
                # Order if necessary
                if self.inventory[component]['quantity'] < component_quantity or self.get_inventory_position(component) < 0:
                    canproduce = False
                    orderqty = production_site.order_quantity(self, self.demand_history[component], self.get_inventory_position(component), component_quantity)
                    if orderqty > 0:
                        self.correct_inventory_position(component, orderqty)
                        if component in self.produced_materials.keys():
                            Log.log(data, self.name, LogType.ORDER, orderqty, component, self.name, None, None, None, None, None)
                            order = Order(self, component, orderqty, None)
                            self.order_management(order, data)
                        else:
                            supplier_route = production_site.select_supplier(self, component, orderqty, data)
                            if supplier_route is None:
                                Log.log(data, self.name, LogType.ORDER, orderqty, component, None, None, None, None, None, 'Lost order')
                            else:
                                cost = data.network_nodes[supplier_route.source].inventory[component]['price'] * orderqty
                                Log.log(data, self.name, LogType.ORDER, orderqty, component, supplier_route.source, supplier_route.mode, cost, self.costcenter, None, None)
                                order = Order(self, component, orderqty, supplier_route)
                                data.network_nodes[supplier_route.source].order_management(order, data)
            self.correct_inventory_position(material, production_quantity)
            if canproduce:
                self.decreaseInventory(material, production_quantity, data)
                data.env.process(self.production(material, production_quantity, data))
            else:
                order = Order(self, material, production_quantity, None)
                self.open_production_orders.append(order)


    def decreaseInventory(self, material, quantity, data):
        for component in data.materials[material].bom.keys():
            component_quantity = data.materials[material].bom[component] * quantity
            # Each component should have enough inventory at this point!
            if self.inventory[component]['quantity'] < component_quantity or self.get_inventory_position(component) < 0:
                raise Exception('Not enough %s at %s: %s/%s' % (component, self.name, self.inventory[component]['quantity'], component_quantity))
            self.change_inventory(component, -component_quantity, data)
            self.correct_inventory_position(component, component_quantity)


    def production(self, material, quantity, data):
        """ Producing materials """
        Log.log(data, self.name, LogType.PRODUCTION_START, quantity, material, None, None, None, None, None, None)
        duration, loss = self.get_disturbance()
        if duration > 0:
            Log.log(data, self.name, LogType.DISTURBANCE, round(quantity * loss), material, None, None, None, None, None, 'Production')
        else:
            duration = 0
        yield data.env.timeout(self.produced_materials[material].time + duration)
        cost = self.produced_materials[material].cost * quantity
        costcenter = self.costcenter
        properties = dict()
        for property in self.produced_materials[material].properties:
            properties[property['property']] = property['value'] * quantity
        # TODO: multiply quantity with 1-loss and change inventory position and new production order if necessary
        Log.log(data, self.name, LogType.PRODUCTION_END, quantity, material, None, None, cost, costcenter, properties, None)
        self.change_inventory(material, quantity, data)
        self.correct_inventory_position(material, -quantity)
        self.check_open_customer_orders(data)

    def check_open_customer_orders(self, data):
        """ Satisfying customer order if possible """
        delivery = True
        while delivery:
            delivery = False
            for order in self.open_customer_orders[:]:
                inventory = self.inventory[order.material]['quantity']
                # if inventory >= order.quantity and self.get_inventory_position(order.material) >= 0:
                if inventory >= order.quantity:
                    self.change_inventory(order.material, -order.quantity, data)
                    self.correct_inventory_position(order.material, order.quantity)
                    self.open_customer_orders.remove(order)
                    delivery = True
                    data.env.process(self.delivery(order, data, False))

    def shipment_receive(self, material, quantity, data):
        """ Ordered components arriving, check if any production can start """
        self.change_inventory(material, quantity, data)
        self.correct_inventory_position(material, -quantity)
        # Check if any production order can be started
        for order in self.open_production_orders[:]:
            canproduce = True
            for component in data.materials[order.material].bom.keys():
                component_quantity = data.materials[order.material].bom[component] * order.quantity
                if self.inventory[component]['quantity'] < component_quantity:
                    canproduce = False
            if canproduce:
                self.open_production_orders.remove(order)
                self.decreaseInventory(order.material, order.quantity, data)
                data.env.process(self.production(order.material, order.quantity, data))


class DistributionCenter(NetworkNode):
    """ Distribution centers serve customers """
    def __init__(self, nn, capacity, properties):
        self.name = nn.name
        self.latitude = nn.latitude
        self.longitude = nn.longitude
        self.costcenter = nn.costcenter
        self.disturbance = nn.disturbance
        self.inventory = nn.inventory
        self.route_starts = nn.route_starts
        self.route_ends = nn.route_ends
        self.validity = nn.validity
        self.demand_history = nn.demand_history
        self.inventory_position_correction = nn.inventory_position_correction
        self.open_customer_orders = nn.open_customer_orders
        self.capacity = capacity
        self.properties = properties

    def order_management(self, order, data):
        """ Handling incoming customer order """
        # TODO: order management without history in order to replace loss of a disturbance
        self.add_demand_history(order.material, order.quantity, data.env.now)
        price = self.inventory[order.material]['price'] * order.quantity
        Log.log(data, self.name, LogType.INCOME, order.quantity, order.material, order.customer.name, None, price, self.costcenter, None, None)
        if self.inventory[order.material]['quantity'] > order.quantity and self.get_inventory_position(order.material) >= order.quantity:
            self.change_inventory(order.material, -order.quantity, data)
            data.env.process(self.delivery(order, data, False))
        else:
            self.correct_inventory_position(order.material, -order.quantity)
            self.open_customer_orders.append(order)
        self.inventory_management(order.material, data, order.quantity)

    def inventory_management(self, material, data, demand_quantity):
        """ Ordering for filling the inventory """
        supplier_qty = distribution_center.order_quantity(self, self.demand_history[material], self.get_inventory_position(material), demand_quantity)
        if supplier_qty > 0:
            supplier_route = distribution_center.select_plant(self, material, supplier_qty, data)
            if supplier_route is None:
                Log.log(data, self.name, LogType.ORDER, supplier_qty, material, None, None, None, None, None, 'Lost order')
            else:
                cost = data.network_nodes[supplier_route.source].inventory[material]['price'] * supplier_qty
                Log.log(data, self.name, LogType.ORDER, supplier_qty, material, supplier_route.source, supplier_route.mode, cost, self.costcenter, None,None)
                self.correct_inventory_position(material, supplier_qty)
                order = Order(self, material, supplier_qty, supplier_route)
                data.network_nodes[supplier_route.source].order_management(order, data)

    def shipment_receive(self, material, quantity, data):
        """ Receiving products from the production plants """
        self.change_inventory(material, quantity, data)
        self.correct_inventory_position(material, -quantity)
        # Checking open orders
        delivery = True
        while delivery:
            delivery = False
            for order in self.open_customer_orders[:]:
                inventory = self.inventory[order.material]['quantity']
                if inventory >= order.quantity and self.get_inventory_position(order.material) >= 0:
                    self.change_inventory(order.material, -order.quantity, data)
                    self.correct_inventory_position(order.material, order.quantity)
                    self.open_customer_orders.remove(order)
                    delivery = True
                    data.env.process(self.delivery(order, data, True))


class Customer(NetworkNode):
    """ Customers generating orders and returns """
    def __init__(self, nn):
        self.name = nn.name
        self.latitude = nn.latitude
        self.longitude = nn.longitude
        self.costcenter = nn.costcenter
        self.disturbance = nn.disturbance
        self.inventory = nn.inventory
        self.route_starts = nn.route_starts
        self.route_ends = nn.route_ends
        self.validity = nn.validity
        self.demand_history = nn.demand_history
        self.inventory_position_correction = nn.inventory_position_correction
        self.open_customer_orders = nn.open_customer_orders
        self.demand = dict()

    def order(self, demand, data):
        """ Ordering and returning products """
        while True:
            if self.is_valid(data.env.now):
                # Order
                qty = distribution.generate_order_quantity(demand, 1, data.env.now)
                if qty > 0:
                    route = customer.select_distribution_center(self, demand, qty, data)
                    if route is None:
                        Log.log(data, self.name, LogType.ORDER, qty, demand.material, None, None, None, None, None, comment='Lost sale')
                    else:
                        cost = data.network_nodes[route.source].inventory[demand.material]['price'] * qty
                        Log.log(data, self.name, LogType.ORDER, qty, demand.material, route.source, route.mode, cost, self.costcenter, None, None)
                        order = Order(self, demand.material, qty, route)
                        data.network_nodes[route.source].order_management(order, data)
                # Return
                qty = distribution.generate_order_quantity(demand, demand.waste_production, data.env.now)
                if qty > 0:
                    order = Order(None, demand.material, qty, customer.select_collection_center(self, data))
                    if order.route is None:
                        Log.log(data, self.name, LogType.RETURN, qty, demand.material, None, None, None, None, None, comment='Lost return')
                    else:
                        order.customer = data.network_nodes[order.route.destination]
                        Log.log(data, self.name, LogType.RETURN, order.quantity, order.material, order.customer.name, None, None, None, None, None)
                        data.env.process(self.delivery(order, data, True))
            yield data.env.timeout(demand.frequency)
            # Print times for debugging
            if PRINT_EVENT_TIMES:
                if data.env.now != data.lastday:
                    if data.env.now % 50 == 0:
                        print()
                    print(data.env.now, end=' ')
                    data.lastday = data.env.now

    def start(self, data):
        """ Starting the demand generating loop """
        for d in self.demand.values():
            data.env.process(self.order(d, data))


class CollectionCenter(NetworkNode):
    """ Collection center collects, stores and transports used products to disassembly plants """
    def __init__(self, nn, capacity, properties):
        self.name = nn.name
        self.latitude = nn.latitude
        self.longitude = nn.longitude
        self.costcenter = nn.costcenter
        self.disturbance = nn.disturbance
        self.inventory = nn.inventory
        self.route_starts = nn.route_starts
        self.route_ends = nn.route_ends
        self.validity = nn.validity
        self.demand_history = nn.demand_history
        self.inventory_position_correction = nn.inventory_position_correction
        self.open_customer_orders = nn.open_customer_orders
        self.capacity = capacity
        self.properties = properties

    def shipment_receive(self, material, quantity, data):
        """ Receiving returned materials and transporting them to disassembly plants if necessary """
        self.change_inventory(material, quantity, data)
        self.add_demand_history(material, quantity, data.env.now)
        qty = collection_center.return_quantity(self, self.demand_history[material], self.inventory[material]['quantity'])
        if qty > 0:
            order = Order(None, material, quantity, collection_center.select_plant(self, material, data))
            if order.route is None:
                Log.log(data, self.name, LogType.RETURN, quantity, material, None, None, None, None, None, comment='Lost return')
            else:
                order.customer = data.network_nodes[order.route.destination]
                Log.log(data, self.name, LogType.RETURN, order.quantity, order.material, order.customer.name, None,None, None, None, None)
                self.change_inventory(order.material, -order.quantity, data)
                data.env.process(self.delivery(order, data, True))


class RecoveryPlant(NetworkNode):
    """ Recovery plants disassembles products into components and supplies to production sites """
    def __init__(self, nn, capacity):
        self.name = nn.name
        self.latitude = nn.latitude
        self.longitude = nn.longitude
        self.costcenter = nn.costcenter
        self.disturbance = nn.disturbance
        self.inventory = nn.inventory
        self.route_starts = nn.route_starts
        self.route_ends = nn.route_ends
        self.validity = nn.validity
        self.demand_history = nn.demand_history
        self.inventory_position_correction = nn.inventory_position_correction
        self.open_customer_orders = nn.open_customer_orders
        self.capacity = capacity
        self.disassembled_materials = dict()


    def decreaseInventory(self, material, quantity, data):
        self.change_inventory(material, -quantity, data)


    def disassembly(self, material, quantity, data):
        """ Disassembling the given quantity of the materials """
        # self.change_inventory(material, -quantity, data)
        Log.log(data, self.name, LogType.DISASSEMBLY_START, quantity, material, None, None, None, None, None,None)
        yield data.env.timeout(self.disassembled_materials[material].time)
        cost = self.disassembled_materials[material].cost * quantity
        costcenter = self.costcenter
        properties = dict()
        for property in self.disassembled_materials[material].properties:
            properties[property['property']] = property['value'] * quantity
        Log.log(data, self.name, LogType.DISASSEMBLY_END, quantity, material, None, None, cost, costcenter, properties, None)
        for component in self.disassembled_materials[material].inverse_bom.keys():
            qty = distribution.generate_disassembly_quantity(self.disassembled_materials[material].inverse_bom[component].quantity_distribution, quantity)
            self.change_inventory(component, qty, data)
        self.check_open_customer_orders(data)


    def check_open_customer_orders(self, data):
        """ Satisfying customer order if possible """
        delivery = True
        while delivery:
            delivery = False
            for order in self.open_customer_orders[:]:
                inventory = self.inventory[order.material]['quantity']
                # if inventory >= order.quantity and self.get_inventory_position(order.material) >= 0:
                if inventory >= order.quantity:
                    self.change_inventory(order.material, -order.quantity, data)
                    self.correct_inventory_position(order.material, order.quantity)
                    self.open_customer_orders.remove(order)
                    delivery = True
                    data.env.process(self.delivery(order, data, False))


    def shipment_receive(self, material, quantity, data):
        """ Receiving returned materials and starting disassembly if necessary """
        self.change_inventory(material, quantity, data)
        self.add_demand_history(material, quantity, data.env.now)
        qty = recovery_plant.disassembly_quantity(self, self.demand_history[material], self.inventory[material]['quantity'])
        if qty > 0:
            self.decreaseInventory(material, qty, data)
            data.env.process(self.disassembly(material, qty, data))

    def order_management(self, order, data):
        """ Handling incoming order from production plants """
        price = self.inventory[order.material]['price'] * order.quantity
        Log.log(data, self.name, LogType.INCOME, order.quantity, order.material, order.customer.name, None, price, self.costcenter, None, None)
        if self.inventory[order.material]['quantity'] < order.quantity:
            # raise Exception('Not enough inventory in the recovery plant')
            self.correct_inventory_position(order.material, -order.quantity)
            self.open_customer_orders.append(order)
        else:
            self.change_inventory(order.material, -order.quantity, data)
            data.env.process(self.delivery(order, data, False))


