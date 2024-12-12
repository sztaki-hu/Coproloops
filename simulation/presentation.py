"""
Copyright   :   Copyright 2024, HUN-REN SZTAKI
File name   :   presentation.py
Description :   User interface for the COPROLOOPS simulation
                Might be changed to Plotly in the future

Revision history:
Date            Author          Comment
----------------------------------------------------------
29/11/2024      Egri            Initial version
"""

import json
import bokeh.plotting
import xyzservices.providers as xyz
from bokeh.plotting import figure, show
from bokeh.models import GeoJSONDataSource, ColumnDataSource, HoverTool, TableColumn, DataTable
from bokeh.layouts import column, gridplot, row
from bokeh.models.callbacks import CustomJS
from bokeh.palettes import Category20c
from bokeh.transform import cumsum
import numpy as np
import pandas as pd
from math import pi
import datastruct
from log import Log


def latlon2mercator(lat, lon):
    """ Converting latitude and longitude into x and y """
    r_major = 6378137.000
    x = r_major * np.radians(lon)
    scale = x / lon
    y = 180.0 / np.pi * np.log(np.tan(np.pi / 4.0 +
                                      lat * (np.pi / 180.0) / 2.0)) * scale
    return (x, y)


def node_color(node):
    """ Color coding the different types of nodes """
    if isinstance(node, datastruct.ProductionSite):
        return 'blue'
    if isinstance(node, datastruct.DistributionCenter):
        return 'saddlebrown'
    if isinstance(node, datastruct.Customer):
        return 'red'
    if isinstance(node, datastruct.CollectionCenter):
        return 'orange'
    if isinstance(node, datastruct.RecoveryPlant):
        return 'green'
    return 'black'


def show_dashboard(nodes, summary):
    """ Showing the simulation results on the dashboard """

    # Map with the nodes and connections
    features = []
    for node in nodes.values():
        x, y = latlon2mercator(node.latitude, node.longitude)
        type = node.get_type()
        feature = {'type': 'Feature', 'id': node.name, 'geometry': {'type': 'Point', 'coordinates': [x, y]},
            'properties': {'name': node.name, 'type': type, 'color': node_color(node)}}
        features.append(feature)
    data = {'type': 'FeatureCollection', 'features': features}
    geo_source = GeoJSONDataSource(geojson=json.dumps(data))
    TOOLTIPS = [
        ('name', '@name'),
        ('type', '@type'),
    ]
    network_map = figure(#x_range=(xmin, xmax), y_range=(ymin, ymax),
               x_axis_type="mercator", y_axis_type="mercator", # tooltips=TOOLTIPS,
               title='COPROLOOPS Simulation',
               active_scroll='wheel_zoom', tools='pan, wheel_zoom, tap')
    network_map.add_tile(xyz.OpenStreetMap.Mapnik)
    scatter = network_map.scatter(x='x', y='y', color='color', size=15, alpha=0.7, source=geo_source, nonselection_fill_alpha=0.3)
    network_map.add_tools(HoverTool(renderers=[scatter], tooltips=TOOLTIPS))
    # Routes
    xs = []
    ys = []
    from_routes = [[] for i in range(len(nodes))]
    to_routes = [[] for i in range(len(nodes))]
    r_index = 0
    for node in nodes.values():
        for route in node.route_starts:
            sx, sy = latlon2mercator(node.latitude, node.longitude)
            dx, dy = latlon2mercator(nodes[route.destination].latitude, nodes[route.destination].longitude)
            xs.append([sx, dx])
            ys.append([sy, dy])
            i = list(nodes.keys()).index(route.source)
            from_routes[i].append(r_index)
            i = list(nodes.keys()).index(route.destination)
            to_routes[i].append(r_index)
            r_index += 1
    linecolor = [None for i in range(len(xs))]
    linealpha = [0.4 for i in range(len(xs))]
    linedata = {'xs': xs, 'ys': ys, 'color': linecolor, 'alpha': linealpha}
    line_source = ColumnDataSource(linedata)
    network_map.multi_line(xs='xs', ys='ys', color='color', alpha='alpha', source=line_source, line_width=2, nonselection_alpha=0.4)
    # Inventories
    # TODO: Show more interesting KPIs instead
    invs = []
    for node in nodes.values():
        mats = []
        qtys = []
        for mat in node.inventory.keys():
            mats.append(mat)
            qtys.append(node.inventory[mat]['quantity'])
        invplot = figure(x_range=mats, title='Inventory at ' + node.name, toolbar_location=None, tools="")
        invplot.vbar(x=mats, top=qtys, width=0.9)
        invplot.visible = False
        invs.append(invplot)
    # Summary table
    summary_tables = []
    for node in nodes.values():
        kpis = ['Cost', 'Income', 'Profit']
        vals = [round(summary[node.name]['cost'], 2), round(summary[node.name]['income'], 2),
                round(summary[node.name]['income'] - summary[node.name]['cost'], 2)] if node.name in summary.keys() else [0, 0, 0]
        for prop in Log.properties:
            kpis.append(prop)
            vals.append(round(summary[node.name][prop], 2) if node.name in summary.keys() else 0)
        temp_table = {'KPI': kpis, 'Value': vals}
        summary_source = ColumnDataSource(pd.DataFrame(temp_table))
        summary_columns = [
            TableColumn(field='KPI', title='KPI'),
            TableColumn(field='Value', title='Value'),
        ]
        summary_table = DataTable(source=summary_source, columns=summary_columns)
        summary_table.visible = False
        summary_tables.append(summary_table)


    network_map.js_on_event('selectiongeometry', CustomJS(args=dict(feat=features, src=geo_source, invs=invs, summary_tables=summary_tables,
                                                          from_routes=from_routes, to_routes=to_routes,
                                                          source=line_source), code="""
        // the event that triggered the callback is cb_obj:
        // The event type determines the relevant attributes
        // console.log('Selection event occurred at : ' + JSON.stringify(cb_obj.geometry))
        for (let i=0; i<invs.length; ++i) {
            invs[i].visible = false
        }
        for (let i=0; i<summary_tables.length; ++i) {
            summary_tables[i].visible = false
        }
        for (let i=0; i<source.data['color'].length; ++i) {
            source.data['color'][i] = null
        }
        for (let i=0; i<src.selected.indices.length; ++i) {
            //invs[src.selected.indices[i]].visible = true
            summary_tables[src.selected.indices[i]].visible = true
            for (let j=0; j<from_routes[src.selected.indices[i]].length; ++j) {
                source.data['color'][from_routes[src.selected.indices[i]][j]] = 'blue'
            }
            for (let j=0; j<to_routes[src.selected.indices[i]].length; ++j) {
                source.data['color'][to_routes[src.selected.indices[i]][j]] = 'green'
            }
        }
        source.change.emit()
        """))

    # Simulation log
    source = ColumnDataSource(pd.DataFrame(Log.get_logtable()))
    formatter = bokeh.models.NumberFormatter(nan_format='')
    columns = [
        TableColumn(field='time', title='Date'),
        TableColumn(field='node', title='Node'),
        TableColumn(field='node_type', title='Node type'),
        TableColumn(field='event', title='Event'),
        TableColumn(field='quantity', title='Quantity'),
        TableColumn(field='material', title='Material'),
        TableColumn(field='node2', title='Node2'),
        TableColumn(field='mode', title='Transportation mode'),
        TableColumn(field='cost', title='Cost', formatter=formatter),
        TableColumn(field='cost_center', title='Cost center')
    ]
    for prop in Log.properties:
        columns.append(TableColumn(field=prop, title=prop, formatter=formatter))
    columns.append(TableColumn(field='comment', title='Comment'))

    # Pie charts
    pie_charts = []
    pie_charts.append(get_chart(summary, 'cost', 'Cost'))
    for prop in Log.properties:
        pie_charts.append(get_chart(summary, prop, prop))

    # Showing the dashboard with all its elements
    show(column(
        row(network_map, gridplot(summary_tables, ncols=2)),
        # row(network_map, gridplot(invs, ncols=2)),
        row(gridplot(pie_charts, ncols=2)),
        DataTable(source=source, columns=columns, width=1600)) #, title='Event log'
    )


def get_chart(summary, field, title):
    """ Creating pie charts for the KPIs """
    chart_dict = dict()
    for costcenter in summary.keys():
        chart_dict[costcenter] = summary[costcenter][field]
    chart_data = pd.Series(chart_dict).reset_index(name='value').rename(columns={'index': 'costcenter'})
    chart_data['angle'] = chart_data['value'] / chart_data['value'].sum() * 2 * pi
    chart_data['color'] = [Category20c[20][i%20] for i in range(len(chart_dict))] # Category20c[len(pie_dict)]
    chart = figure(height=350, title=title, toolbar_location=None,
               tools="hover", tooltips="@costcenter: @value", x_range=(-0.5, 1.0))
    chart.wedge(x=0, y=1, radius=0.4,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color="white", fill_color='color', legend_field='costcenter', source=chart_data)
    chart.axis.axis_label = None
    chart.axis.visible = False
    chart.grid.grid_line_color = None
    return chart
