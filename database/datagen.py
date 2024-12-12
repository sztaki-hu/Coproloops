import random
import sqlite3
import networkx as nx
import datetime


# MATERIALS
NRMATERIAL = 10                     # Number of materials
MATHIERARCHYPROB = 0.4              # Probability of a link between two materials
MINVOLUME = 1                       # Minimum volume of a material
MAXVOLUME = 100                     # Maximum volume of a material
MINMASS = 0.1                       # Minimum mass of a material
MAXMASS = 5.0                       # Maximum mass of a material
MINBOMQTY = 1                       # Minimum required quantity in a BOM
MAXBOMQTY = 10                      # Maximum required quantity in a BOM
MATERIALPROPERTYPROB = 0.1          # Probability that a raw material has a property
# NETWORK NODES
DISTURBANCEPROB = 0.05              # Probability of a network node disturbance
DISTURBANCELOSS = 0.1               # Loss during a network node disturbance
DISTURBANCEAVG = 10                 # Average length of a network node disturbance
DISTURBANCESTD = 5                  # Standard deviation length of a network node disturbance
RELATIVEFREQ = [10, 5, 20, 5, 2]    # Relative frequencies of production plants, dcs, customers, collection centers and recovery plants
MINCAPACITY = 50                    # Minimum capacity of a network node
MAXCAPACITY = 500                   # Maximum capacity of a network node
MINENERGY = 10                      # Minimum energy consumption of a network node
MAXENERGY = 100                     # Maximum energy consumption of a network node
MININVENTORY = 0                    # Minimum initial inventory
MAXINVENTORY = 1000                 # Maximum initial inventory
VALIDITYPROB = 0.1                  # Probability that a network node has a validity
# PRODUCTION
PRODPROBABILITY = 0.2               # Probability that a material is produced at a plant
MINPRODCOST = 1                     # Minimum production cost of a material
MAXPRODCOST = 10                    # Maximum production cost of a material
MINPRODEMISSION = 0                 # Minimum emission of a material production
MAXPRODEMISSION = 0.4               # Maximum emission of a material production
MINPRODENERGY = 0                   # Minimum energy consumption of a material production
MAXPRODENERGY = 0.4                 # Maximum energy consumption of a material production
MINPRODWATER = 0                    # Minimum water consumption of a material production
MAXPRODWATER = 0.4                  # Maximum water consumption of a material production
MINPRODTIME = 1                     # Minimum production time
MAXPRODTIME = 10                    # Maximum production time
MINPRODCAPACITY = 1                 # Minimum capacity usage of a material production
MAXPRODCAPACITY = 3                 # Maximum capacity usage of a material production
PROFITRATE = 1.8                    # Approximate profit rate on a produced material
EPSILON = 0.05                      # Variation of the product prices at different plants
# DISASSEMBLY
DISASSEMBLYPROBABILITY = 0.8        # Probability that a material is disassembled at a recovery plant
MINDISASSEMBLYCOST = 1              # Minimum disassembly cost of a material
MAXDISASSEMBLYCOST = 5              # Maximum disassembly cost of a material
MINDISASSEMBLYEMISSION = 0          # Minimum emission of a material disassembly
MAXDISASSEMBLYEMISSION = 0.4        # Maximum emission of a material disassembly
MINDISASSEMBLYENERGY = 0            # Minimum energy consumption of a material disassembly
MAXDISASSEMBLYENERGY = 0.4          # Maximum energy consumption of a material disassembly
MINDISASSEMBLYWATER = 0             # Minimum water consumption of a material disassembly
MAXDISASSEMBLYWATER = 0.4           # Maximum water consumption of a material disassembly
MINDISASSEMBLYTIME = 1              # Minimum disassembly time
MAXDISASSEMBLYTIME = 5              # Maximum disassembly time
MINDISASSEMBLYCAPACITY = 1          # Minimum capacity usage of a material disassembly
MAXDISASSEMBLYCAPACITY = 3          # Maximum capacity usage of a material disassembly
PRICEDISCOUNT = 0.5                 # Price ratio between disassembled and produced materials
# DEMAND
DEMANDPROBABILITY = 0.7             # Probability that a customer requires a finished good
MINDEMANDFREQUENCY = 1              # Minimum ordering frequency
MAXDEMANDFREQUENCY = 10             # Maximum ordering frequency
BACKLOGPROBABILITY = 0.5            # Probability that backlog is accepted
MINDEMANDADDTREND = 0               # Minimum additional trend of the demand
MAXDEMANDADDTREND = 20              # Maximum additional trend of the demand
MINDEMANDMULTREND = 0.9             # Minimum multiplicative trend of the demand
MAXDEMANDMULTREND = 1.3             # Maximum multiplicative trend of the demand
MINWASTE = 0                        # Minimum percent of non-reused finished goods
MAXWASTE = 1                        # Minimum percent of non-reused finished goods
MINDEMANDAVG = 10                   # Minimum average of the demand
MAXDEMANDAVG = 100                  # Maximum average of the demand
MINDEMANDSTD = 1                    # Minimum standard deviation of the demand
MAXDEMANDSTD = 5                    # Maximum standard deviation of the demand
MINDUEDATE = 1                      # Minimum due date for orders
MAXDUEDATE = 15                     # Maximum due date for orders


NODES = [
    {'name': 'Lisbon', 'latitude': 38.7253, 'longitude': -9.15},
    {'name': 'Madrid', 'latitude': 40.4169, 'longitude': -3.7033},
    {'name': 'Andorra la Vella', 'latitude': 42.5, 'longitude': 1.5},
    {'name': 'Paris', 'latitude': 48.8567, 'longitude': 2.3522},
    {'name': 'The Hague', 'latitude': 52.08, 'longitude': 4.31},
    {'name': 'Brussels', 'latitude': 50.8467, 'longitude': 4.3525},
    {'name': 'Amsterdam', 'latitude': 52.3728, 'longitude': 4.8936},
    {'name': 'Luxembourg', 'latitude': 49.6117, 'longitude': 6.1319},
    {'name': 'Monaco', 'latitude': 43.7333, 'longitude': 7.4167},
    {'name': 'Bern', 'latitude': 46.9481, 'longitude': 7.4475},
    {'name': 'Vaduz', 'latitude': 47.141, 'longitude': 9.521},
    {'name': 'Oslo', 'latitude': 59.9133, 'longitude': 10.7389},
    {'name': 'San Marino', 'latitude': 43.9346, 'longitude': 12.4473},
    {'name': 'Rome', 'latitude': 41.8931, 'longitude': 12.4828},
    {'name': 'Copenhagen', 'latitude': 55.6761, 'longitude': 12.5683},
    {'name': 'Berlin', 'latitude': 52.52, 'longitude': 13.405},
    {'name': 'Prague', 'latitude': 50.0875, 'longitude': 14.4214},
    {'name': 'Ljubljana', 'latitude': 46.0514, 'longitude': 14.5061},
    {'name': 'Zagreb', 'latitude': 45.8167, 'longitude': 15.9833},
    {'name': 'Vienna', 'latitude': 48.2083, 'longitude': 16.3725},
    {'name': 'Bratislava', 'latitude': 48.1439, 'longitude': 17.1097},
    {'name': 'Stockholm', 'latitude': 59.3294, 'longitude': 18.0686},
    {'name': 'Sarajevo', 'latitude': 43.8564, 'longitude': 18.4131},
    {'name': 'Budapest', 'latitude': 47.4925, 'longitude': 19.0514},
    {'name': 'Podgorica', 'latitude': 42.4413, 'longitude': 19.2629},
    {'name': 'Tirana', 'latitude': 41.3289, 'longitude': 19.8178},
    {'name': 'Belgrade', 'latitude': 44.82, 'longitude': 20.46},
    {'name': 'Warsaw', 'latitude': 52.23, 'longitude': 21.0111},
    {'name': 'Pristina', 'latitude': 42.6633, 'longitude': 21.1622},
    {'name': 'Skopje', 'latitude': 41.9961, 'longitude': 21.4317},
    {'name': 'Sofia', 'latitude': 42.7, 'longitude': 23.33},
    {'name': 'Athens', 'latitude': 37.9842, 'longitude': 23.7281},
    {'name': 'Riga', 'latitude': 56.9489, 'longitude': 24.1064},
    {'name': 'Tallinn', 'latitude': 59.4372, 'longitude': 24.7453},
    {'name': 'Helsinki', 'latitude': 60.1708, 'longitude': 24.9375},
    {'name': 'Vilnius', 'latitude': 54.6872, 'longitude': 25.28},
    {'name': 'Bucharest', 'latitude': 44.4325, 'longitude': 26.1039},
    {'name': 'Minsk', 'latitude': 53.9, 'longitude': 27.5667},
    {'name': 'Chisinau', 'latitude': 47.0228, 'longitude': 28.8353},
    {'name': 'Kyiv', 'latitude': 50.45, 'longitude': 30.5233},
    {'name': 'Ankara', 'latitude': 39.93, 'longitude': 32.85},
    {'name': 'Dublin', 'latitude': 53.3331, 'longitude': -6.2489},
    {'name': 'London', 'latitude': 51.5085, 'longitude': -0.1257}]

TRANSPORTMODES = [
    {'name': 'Truck', 'fixcost': 100, 'distancecost': 0.5, 'emission': 0.1, 'energy': 0.2, 'time': 0.5},
    {'name': 'Parcel', 'fixcost': 10000, 'distancecost': 0, 'emission': 0.1, 'energy': 0, 'time': 5}]

MATERIALPROPERTIES = ['Hazardous', 'Biological', 'Recyclable', 'Packaging']

OPERATIONPROPERTIES = ['Emission', 'Energy', 'Water']


def emptyDB(cursor):
    cursor.execute("DELETE FROM MaterialPropertyLink")
    cursor.execute("DELETE FROM MaterialProperty")
    cursor.execute("DELETE FROM OperationPropertyLink")
    cursor.execute("DELETE FROM OperationPropertyClass")
    cursor.execute("DELETE FROM OperationProperty")
    cursor.execute("DELETE FROM Validity")
    cursor.execute("DELETE FROM Demand")
    cursor.execute("DELETE FROM Inventory")
    cursor.execute("DELETE FROM InverseBOM")
    cursor.execute("DELETE FROM DisassembledMaterial")
    cursor.execute("DELETE FROM ProducedMaterial")
    cursor.execute("DELETE FROM ProductionSite")
    cursor.execute("DELETE FROM DistributionCenter")
    cursor.execute("DELETE FROM Customer")
    cursor.execute("DELETE FROM CollectionCenter")
    cursor.execute("DELETE FROM RecoveryPlant")
    cursor.execute("DELETE FROM Route")
    cursor.execute("DELETE FROM TransportMode")
    cursor.execute("DELETE FROM NetworkNode")
    cursor.execute("DELETE FROM CostCenter")
    cursor.execute("DELETE FROM BOM")
    cursor.execute("DELETE FROM Material")
    cursor.execute("DELETE FROM Distribution")
    cursor.execute("DELETE FROM Disturbance")


def genMatPrices(mat, bom, prices, prodcosts):
    if mat in prices:
        return prices[mat]
    cost = 0
    for b in bom:
        if mat == b["product"]:
            compprice = genMatPrices(b["component"], bom, prices, prodcosts)
            cost += compprice * b["quantity"]
    prices[mat] = (cost + prodcosts[mat]) * PROFITRATE
    return prices[mat]


def genMaterialHierarchy(cursor):
    for prop in MATERIALPROPERTIES:
        cursor.execute("INSERT INTO MaterialProperty (Name) VALUES (?)", (prop, ))
    rawmats = set()
    fgmats = set()
    prodcosts = dict()
    for i in range(NRMATERIAL):
        vol = random.randint(MINVOLUME, MAXVOLUME)
        mass = random.uniform(MINMASS, MAXMASS)
        mat = "MAT" + str(i).zfill(4)
        prodcosts[mat] = random.uniform(MINPRODCOST, MAXPRODCOST)
        rawmats.add(mat)
        fgmats.add(mat)
        cursor.execute("INSERT INTO Material (Name, Volume, Mass) VALUES (?, ?, ?)", (mat, vol, mass))
    G = nx.gnp_random_graph(NRMATERIAL, MATHIERARCHYPROB, directed=True)
    bom = []
    for edge in G.edges:
        if edge[0] < edge[1]:
            prod = "MAT" + str(edge[0]).zfill(4)
            comp = "MAT" + str(edge[1]).zfill(4)
            rawmats.discard(prod)
            fgmats.discard(comp)
            qty = random.randint(MINBOMQTY, MAXBOMQTY)
            bom.append({'product': prod, 'component': comp, 'quantity': qty})
            cursor.execute("INSERT INTO BOM (Product, Component, Quantity) VALUES (?, ?, ?)", (prod, comp, qty))
    prices = dict()
    for i in range(NRMATERIAL):
        mat = "MAT" + str(i).zfill(4)
        genMatPrices(mat, bom, prices, prodcosts)
    for mat in rawmats:
        for prop in MATERIALPROPERTIES:
            if random.random() < MATERIALPROPERTYPROB:
                cursor.execute("INSERT INTO MaterialPropertyLink (MaterialName, MaterialPropertyName) VALUES (?, ?)", (mat, prop))
    return rawmats, fgmats, prodcosts, prices, bom


def genDisturbance(cursor, avg, std, prob, loss):
    cursor.execute("INSERT INTO Distribution (Type, Avg, Std) VALUES ('normal', ?, ?)", (avg, std))
    rowid = cursor.lastrowid
    cursor.execute("INSERT INTO Disturbance (Probability, Duration, Loss) VALUES (?, ?, ?)", (prob, rowid, loss))
    return cursor.lastrowid


def genOperationPropertyTypes(cursor):
    for prop in OPERATIONPROPERTIES:
        cursor.execute("INSERT INTO OperationProperty (Name) VALUES (?)", (prop, ))


def genNetworkNodes(cursor, disturbanceID):
    for node in NODES:
        cursor.execute("INSERT INTO CostCenter (Name) VALUES (?)", (node["name"], ))
        cursor.execute("INSERT INTO NetworkNode (Name, Latitude, Longitude, CostCenter, DisturbanceID) VALUES (?, ?, ?, ?, ?)",
                       (node["name"],  node["latitude"], node["longitude"], node["name"], disturbanceID))


def genValidity(cursor):
    now = datetime.datetime.now()
    for node in NODES:
        if random.random() < VALIDITYPROB:
            if random.random() < 0.5:
                cursor.execute("INSERT INTO Validity (NetworkNode, Start) VALUES (?, ?)", (node["name"], now + datetime.timedelta(weeks=4)))
            else:
                cursor.execute("INSERT INTO Validity (NetworkNode, End) VALUES (?, ?)", (node["name"], now + datetime.timedelta(weeks=52)))


def genNetworkNodeTypes(cursor):
    prodplants = []
    dcs = []
    customers = []
    ccs = []
    recovplants = []
    # Normalizing frequencies
    total = sum(RELATIVEFREQ)
    for i in range(len(RELATIVEFREQ)):
        RELATIVEFREQ[i] /= total
        if i > 0:
            RELATIVEFREQ[i] += RELATIVEFREQ[i-1]
    while 0 == len(prodplants) or 0 == len(dcs) or 0 == len(customers) or 0 == len(ccs) or 0 == len(recovplants):
        prodplants = []
        dcs = []
        customers = []
        ccs = []
        recovplants = []
        for node in NODES:
            rnd = random.random()
            if rnd < RELATIVEFREQ[0]:
                prodplants.append(node)
            elif rnd < RELATIVEFREQ[1]:
                dcs.append(node)
            elif rnd < RELATIVEFREQ[2]:
                customers.append(node)
            elif rnd < RELATIVEFREQ[3]:
                ccs.append(node)
            else:
                recovplants.append(node)
    for node in prodplants:
        cap = random.randint(MINCAPACITY, MAXCAPACITY)
        cursor.execute("INSERT INTO ProductionSite (NetworkNode, CapacityLimit) VALUES (?, ?)", (node["name"], cap))
    for node in dcs:
        cap = random.randint(MINCAPACITY, MAXCAPACITY)
        nrg = random.randint(MINENERGY, MAXENERGY)
        cursor.execute("INSERT INTO OperationPropertyClass DEFAULT VALUES")
        rowid = cursor.lastrowid
        cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Energy', nrg))
        cursor.execute("INSERT INTO DistributionCenter (NetworkNode, CapacityLimit, OperationPropertyID) VALUES (?, ?, ?)", (node["name"], cap, rowid))
    for node in customers:
        cursor.execute("INSERT INTO Customer (NetworkNode) VALUES (?)", (node["name"], ))
    for node in ccs:
        cap = random.randint(MINCAPACITY, MAXCAPACITY)
        nrg = random.randint(MINENERGY, MAXENERGY)
        cursor.execute("INSERT INTO OperationPropertyClass DEFAULT VALUES")
        rowid = cursor.lastrowid
        cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Energy', nrg))
        cursor.execute("INSERT INTO CollectionCenter (NetworkNode, CapacityLimit, OperationPropertyID) VALUES (?, ?, ?)", (node["name"], cap, rowid))
    for node in recovplants:
        cap = random.randint(MINCAPACITY, MAXCAPACITY)
        cursor.execute("INSERT INTO RecoveryPlant (NetworkNode, CapacityLimit) VALUES (?, ?)", (node["name"], cap))
    return prodplants, dcs, customers, ccs, recovplants


def genTransportModes(cursor, disturbanceID):
    for mode in TRANSPORTMODES:
        cursor.execute("INSERT INTO OperationPropertyClass DEFAULT VALUES")
        rowid = cursor.lastrowid
        cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Emission', mode["emission"]))
        cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Energy', mode["energy"]))
        cursor.execute("INSERT INTO TransportMode (Name, FixedCost, DistanceCost, Time, DisturbanceID, OperationPropertyID) VALUES (?, ?, ?, ?, ?, ?)",
            (mode["name"], mode["fixcost"], mode["distancecost"], mode["time"], disturbanceID, rowid))


def genRoute(cursor, node1, node2):
    if node1 != node2:
        for mode in TRANSPORTMODES:
            cursor.execute("INSERT INTO Route (Source, Destination, TransportMode, CostCenter) VALUES (?, ?, ?, ?)",
                           (node1["name"], node2["name"], mode["name"], node1["name"]))


def genRoutes(cursor, prodplants, dcs, customers, ccs, recovplants):
    for node1 in prodplants:
        for node2 in prodplants:
            genRoute(cursor, node1, node2)
        for node2 in dcs:
            genRoute(cursor, node1, node2)
    for node1 in dcs:
        for node2 in dcs:
            genRoute(cursor, node1, node2)
        for node2 in customers:
            genRoute(cursor, node1, node2)
    for node1 in customers:
        for node2 in ccs:
            genRoute(cursor, node1, node2)
    for node1 in ccs:
        for node2 in ccs:
            genRoute(cursor, node1, node2)
        for node2 in recovplants:
            genRoute(cursor, node1, node2)
    for node1 in recovplants:
        # for node2 in recovplants:
        #     genRoute(cursor, node1, node2)
        for node2 in prodplants:
            genRoute(cursor, node1, node2)


def genProducedMaterials(cursor, prodplants, prodcosts, prices):
    producedmats = []
    for i in range(NRMATERIAL):
        mat = "MAT" + str(i).zfill(4)
        isProduced = False
        while not isProduced:
            for plant in prodplants:
                if random.random() < PRODPROBABILITY:
                    producedmats.append({'node': plant["name"], 'mat': mat})
                    cost = prodcosts[mat] * random.uniform(1-EPSILON, 1+EPSILON)
                    emission = random.uniform(MINPRODEMISSION, MAXPRODEMISSION)
                    nrg = random.uniform(MINPRODENERGY, MAXPRODENERGY)
                    water = random.uniform(MINPRODWATER, MAXPRODWATER)
                    time = random.randint(MINPRODTIME, MAXPRODTIME)
                    capacity = random.randint(MINPRODCAPACITY, MAXPRODCAPACITY)
                    price = prices[mat] * random.uniform(1-EPSILON, 1+EPSILON)
                    cursor.execute("INSERT INTO OperationPropertyClass DEFAULT VALUES")
                    rowid = cursor.lastrowid
                    cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Emission', emission))
                    cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Energy', nrg))
                    cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Water', water))
                    cursor.execute("INSERT INTO ProducedMaterial (ProductionSite, MaterialName, Cost," +
                        "Time, CapacityUsage, Price, OperationPropertyID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (plant["name"], mat, cost, time, capacity, price, rowid))
                    isProduced = True
    return producedmats


def genDisassembly(cursor, fgmats, recovplants, prices, bom):
    disassembledmats = []
    for mat in fgmats:
        for plant in recovplants:
            if random.random() < DISASSEMBLYPROBABILITY:
                disassembledmats.append({'node': plant["name"], 'mat': mat})
                cost = random.uniform(MINDISASSEMBLYCOST, MAXDISASSEMBLYCOST)
                emission = random.uniform(MINDISASSEMBLYEMISSION, MAXDISASSEMBLYEMISSION)
                nrg = random.uniform(MINDISASSEMBLYENERGY, MAXDISASSEMBLYENERGY)
                water = random.uniform(MINDISASSEMBLYWATER, MAXDISASSEMBLYWATER)
                time = random.randint(MINDISASSEMBLYTIME, MAXDISASSEMBLYTIME)
                capacity = random.randint(MINDISASSEMBLYCAPACITY, MAXDISASSEMBLYCAPACITY)
                cursor.execute("INSERT INTO OperationPropertyClass DEFAULT VALUES")
                rowid = cursor.lastrowid
                cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Emission', emission))
                cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Energy', nrg))
                cursor.execute("INSERT INTO OperationPropertyLink (ClassID, OperationProperty, Value) VALUES (?, ?, ?)", (rowid, 'Water', water))
                cursor.execute("INSERT INTO DisassembledMaterial (Product, RecoveryPlant, Cost," +
                    "Time, CapacityUsage, OperationPropertyID) VALUES (?, ?, ?, ?, ?, ?)",
                    (mat, plant["name"], cost, time, capacity, rowid))
                for b in bom:
                    if mat == b["product"]:
                        cursor.execute("INSERT INTO Distribution (Type, Min, Max) VALUES ('uniform', 0, ?)", (b["quantity"], ))
                        rowid = cursor.lastrowid
                        price = prices[b["component"]] * PRICEDISCOUNT
                        cursor.execute("INSERT INTO InverseBOM (Product, RecoveryPlant, Component, Quantity, Price) VALUES (?, ?, ?, ?, ?)",
                            (mat, plant["name"], b["component"], rowid, price))
    return disassembledmats


# Generating produced and disassembled products and components
def genNodeInventory(node, mats, bom):
    inv = dict()
    for dat in mats:
        if node["name"] == dat["node"]:
            inv[dat["mat"]] = random.randint(MININVENTORY, MAXINVENTORY)
            for b in bom:
                if dat["mat"] == b["product"]:
                    inv[b["component"]] = random.randint(MININVENTORY, MAXINVENTORY) * b["quantity"]
    return inv


def genInventory(cursor, producedmats, disassembledmats, prodplants, recovplants, bom, dcs, ccs, fgmats, prices):
    for plant in prodplants:
        inv = genNodeInventory(plant, producedmats, bom)
        for invkey in inv.keys():
            price = prices[invkey] * random.uniform(1-EPSILON, 1+EPSILON)
            cursor.execute("INSERT INTO Inventory (Material, NetworkNode, Quantity, Price) VALUES (?, ?, ?, ?)", (invkey, plant["name"], inv[invkey], price))
    for plant in recovplants:
        inv = genNodeInventory(plant, disassembledmats, bom)
        for invkey in inv.keys():
            price = prices[invkey] * random.uniform(1-EPSILON, 1+EPSILON)
            cursor.execute("INSERT INTO Inventory (Material, NetworkNode, Quantity, Price) VALUES (?, ?, ?, ?)", (invkey, plant["name"], inv[invkey], price))
    for mat in fgmats:
        for dc in dcs:
            qty = random.randint(MININVENTORY, MAXINVENTORY)
            price = prices[mat] * random.uniform(1-EPSILON, 1+EPSILON)
            cursor.execute("INSERT INTO Inventory (Material, NetworkNode, Quantity, Price) VALUES (?, ?, ?, ?)", (mat, dc["name"], qty, price))
        for cc in ccs:
            qty = random.randint(MININVENTORY, MAXINVENTORY)
            # price = prices[mat] * random.uniform(1-EPSILON, 1+EPSILON)
            cursor.execute("INSERT INTO Inventory (Material, NetworkNode, Quantity, Price) VALUES (?, ?, ?, ?)", (mat, cc["name"], qty, 0))


def genDemand(cursor, customers, fgmats):
    for customer in customers:
        for product in fgmats:
            if random.random() < DEMANDPROBABILITY:
                freq = random.randint(MINDEMANDFREQUENCY, MAXDEMANDFREQUENCY)
                backlog = 0
                if random.random() < BACKLOGPROBABILITY:
                    backlog = 1
                addtrend = random.uniform(MINDEMANDADDTREND, MAXDEMANDADDTREND)
                multrend = random.uniform(MINDEMANDMULTREND, MAXDEMANDMULTREND)
                waste = random.uniform(MINWASTE, MAXWASTE)
                avg = random.uniform(MINDEMANDAVG, MAXDEMANDAVG)
                std = random.uniform(MINDEMANDSTD, MAXDEMANDSTD)
                duedate = random.randrange(MINDUEDATE, MAXDUEDATE)
                cursor.execute("INSERT INTO Distribution (Type, Avg, Std) VALUES ('normal', ?, ?)", (avg, std))
                rowid = cursor.lastrowid
                cursor.execute("INSERT INTO Demand (Customer, Material, Frequency, Quantity, IsBacklog, AdditionalTrend," +
                    "MultiplicativeTrend, Duedate, WasteProduction) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (customer["name"], product, freq, rowid, backlog, addtrend, multrend, duedate, waste))


def main():
    conn = sqlite3.connect("simulationdb")
    cursor = conn.cursor()
    emptyDB(cursor)
    rawmats, fgmats, prodcosts, prices, bom = genMaterialHierarchy(cursor)
    disturbanceID = genDisturbance(cursor, DISTURBANCEAVG, DISTURBANCESTD, DISTURBANCEPROB, DISTURBANCELOSS)
    genOperationPropertyTypes(cursor)
    genNetworkNodes(cursor, disturbanceID)
    genValidity(cursor)
    prodplants, dcs, customers, ccs, recovplants = genNetworkNodeTypes(cursor)
    genTransportModes(cursor, disturbanceID)
    genRoutes(cursor, prodplants, dcs, customers, ccs, recovplants)
    producedmats = genProducedMaterials(cursor, prodplants, prodcosts, prices)
    disassembledmats = genDisassembly(cursor, fgmats, recovplants, prices, bom)
    genInventory(cursor, producedmats, disassembledmats, prodplants, recovplants, bom, dcs, ccs, fgmats, prices)
    genDemand(cursor, customers, fgmats)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
