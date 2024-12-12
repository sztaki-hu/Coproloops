"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   distribution.py
Description :   Statistical distributions for the COPROLOOPS simulation

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
"""
from numpy import random

# Trends increase monthly
TREND_PERIODICITY = 30


class InvalidDistributionError(Exception):
	pass


def random_from_distribution(distribution):
	""" Generating value from a statistical distribution """
	if 'uniform' == distribution.type:
		if distribution.min is None or distribution.max is None:
			raise InvalidDistributionError()
		return random.uniform(distribution.min, distribution.max)
	if 'normal' == distribution.type:
		if distribution.avg is None or distribution.std is None:
			raise InvalidDistributionError()
		return random.normal(distribution.avg, distribution.std)
	raise InvalidDistributionError()


def generate_order_quantity(demand, multiplier, now):
	""" Generating demand considering trend """
	qty = None
	try:
		qty = random_from_distribution(demand.quantity_distribution)
	except InvalidDistributionError:
		print('Error with distribution')
	if qty is not None:
		period = now / TREND_PERIODICITY
		qty = (qty * pow(demand.multiplicative_trend, period) + demand.additional_trend * period) * multiplier
		qty = round(qty)
		return qty
	return 0


def generate_disassembly_quantity(distribution, multiplier):
	""" Generating component quantity from the disassembled product quantity """
	qty = None
	try:
		qty = random_from_distribution(distribution)
	except InvalidDistributionError:
		print('Error with distribution')
	if qty is not None:
		return round(qty * multiplier)
	return 0
