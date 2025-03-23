from __future__ import annotations

import networkx as nx
import shapely
import copy
from itertools import pairwise

import constants as cs
import general_maths as gm
from points import Point
from polygons import Polygon


class Route:
    def __init__(self, points: list[Point]):
        self.points = points[1:]
        self.length = 0
        self.calculate_length()

    def __repr__(self) -> str:
        return str(self.points)

    def __len__(self) -> float:
        return self.length

    def reached_point(self) -> None:
        self.points.pop(0)

    def next_point(self) -> Point | None:
        if len(self.points) > 0:
            return self.points[0]
        else:
            return None

    def calculate_length(self) -> None:
        for i, j in pairwise(self.points):
            self.length += i.distance_to_point(j)


def is_visible(p1: Point, p2: Point, obstacles: list[Polygon]) -> bool:
    """
    Checks if p1 and p2 are visible to each other for a set of obstacles
    :param p1:
    :param p2:
    :param obstacles:
    :return:
    """
    line = shapely.LineString([p1.shapely, p2.shapely])
    for obs in obstacles:
        if line.crosses(obs.shapely) or obs.shapely.contains(line):
            return False
    return True


def create_base_graph(obstacles: list[Polygon]) -> nx.Graph:
    visibility_graph = nx.Graph()
    vertices = [point for obstacle in obstacles for point in obstacle.points]

    for v1 in vertices:
        for v2 in vertices:
            if v1 != v2 and is_visible(v1, v2, obstacles):
                distance = gm.calculate_distance(v1, v2)
                visibility_graph.add_edge(v1, v2, weight=distance)
    return visibility_graph


def add_point_to_graph(point: Point, obstacles: list[Polygon], graph: nx.Graph) -> nx.Graph:
    vertices = [point for obstacle in obstacles for point in obstacle.points]
    for vertex in vertices:
        if point != vertex and is_visible(point, vertex, obstacles):
            distance = gm.calculate_distance(point, vertex)
            graph.add_edge(point, vertex, weight=distance)
    return graph


def make_route_from_path(path: list[Point]) -> Route:
    return Route(path)


def create_route(start: Point, end: Point) -> Route:
    obstacles = cs.world.landmasses
    world_graph = cs.world.visibility_graph
    graph = copy.copy(world_graph)
    graph = add_point_to_graph(start, obstacles, graph)
    graph = add_point_to_graph(end, obstacles, graph)

    shortest_path = nx.shortest_path(graph, source=start, target=end, weight='weight')
    return make_route_from_path(shortest_path)
