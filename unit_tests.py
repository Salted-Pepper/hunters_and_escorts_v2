from polygons import Polygon
from points import Point
import routes
import constants as cs


def routing_test() -> None:
    obstacles = [
        Polygon([Point(2, 2), Point(3, 3), Point(4, 3.5), Point(4, 4), Point(2, 4)]),
        Polygon([Point(6, 6), Point(8, 6), Point(8, 8), Point(6, 8)]),
    ]
    cs.world.current_graph = routes.create_base_graph(obstacles)
    start = Point(0, 0)
    end = Point(10, 10)
    route = routes.create_route(start=start, end=end)
    print(f"Created route: {repr(route)}")


def run_tests() -> None:
    routing_test()


run_tests()
