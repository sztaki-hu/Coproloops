"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   recovery_plant.py
Description :   Sample decision logic of recovery plants for the COPROLOOPS simulation

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
"""

# Multipliers for the inventory policy (related to the average demand)
S_MULTIPLIER = 10


def disassembly_quantity(recovery, history, inventory):
    """ Disassembling all materials in the inventory if it is above the target level """
    S = getS(recovery, history)
    if inventory < S:
        return 0
    return inventory


def getS(recovery, history):
    """ Sample target level for the recovery plant
        Average demand multiplied by a constant, independently of the plant
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

