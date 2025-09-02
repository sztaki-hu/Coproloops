"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   coproloops.py
Description :   Main file for the COPROLOOPS simulation

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
02/09/2025      Egri            First public version
"""

import datastruct
import simpy
import datetime
from log import Log
import presentation

# Simulation model data
DATABASE = 'simulationdb'
# Simulation horizon
HORIZON = 365


def main():
    """ Initializing and starting the simulation """
    # starttime = datetime.datetime(2024, 3, 23)
    starttime = datetime.datetime.today()
    Log.starttime = starttime
    env = simpy.Environment()
    data = datastruct.DataStructure(DATABASE, starttime, env)
    # Starting the customers
    for node in data.network_nodes.values():
        if isinstance(node, datastruct.Customer):
            node.start(data)
    try:
        env.run(until=HORIZON)
    finally:
        # Log.print_logs()
        # Log.save_log('log.csv')
        pass

    # Printing simulation log and KPIs
    print()
    summary = Log.get_summary()
    s = 'Cost_center'.ljust(15) + 'Cost'.ljust(15) + 'Income'.ljust(15) + 'Profit'.ljust(15)
    for p in Log.properties:
        s += p.ljust(15)
    print(s)
    for costcenter in summary.keys():
        s = costcenter.replace(' ', '_').ljust(15) + str(round(summary[costcenter]['cost'], 2)).ljust(15) + str(round(summary[costcenter]['income'], 2)).ljust(15)
        s += str(round(summary[costcenter]['income'] - summary[costcenter]['cost'], 2)).ljust(15)
        for p in Log.properties:
            s += str(round(summary[costcenter][p], 2)).ljust(15)
        print(s)

    # Print inventories
    # for node in data.network_nodes.values():
    #     for mat in node.inventory.keys():
    #         if node.inventory[mat]['quantity'] > 0:
    #             print(node.name, mat, node.inventory[mat]['quantity'])

    # Showing simulation results on the dashboard
    presentation.show_dashboard(data.network_nodes, summary)


if __name__ == '__main__':
    main()
