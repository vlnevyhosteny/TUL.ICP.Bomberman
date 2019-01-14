import json

from src.map.border import Border
from src.map.cube import Cube
from src.map.cube_style import CubeStyle
from src.map.field_cube import FieldCube
from src.map.floor_cube import FloorCube
from src.map.map import Map


def parse_map_from_json_file(path_to_json):
    try:
        with open(path_to_json, 'r') as json_file:
            data = json_file.read()
            parsed = json.loads(data)

            name = parsed['name']
            width = parsed['width']
            height = parsed['height']
            border = parse_border_from_json(parsed['border'])
            floor_cubes = parse_floor_cubes_from_json(parsed['floor_cubes'])
            cubes = parse_field_cubes_from_json(parsed['cubes'])
            cube_styles = parse_cube_styles_from_json(parsed['cube_styles'])

            return Map(name, width, height, cubes, cube_styles, floor_cubes, border)
    except IOError:
        print('An error occured trying to read the file.')
    except ValueError:
        print('Unable to parse data in the file.')
    except Exception:
        print('Unable to load map. [' + path_to_json + ']')


def parse_border_from_json(json_data):
    return Border(json_data['color'], json_data['texture'])


def parse_floor_cubes_from_json(json_data):
    cubes = []

    for cube in json_data:
        floor_cube = parse_floor_cube_from_json(cube)
        cubes.append(floor_cube)

    return cubes


def parse_floor_cube_from_json(json_data):
    base_cube = parse_cube_from_json(json_data)
    return FloorCube(base_cube.position_x, base_cube.position_y, base_cube.style_id)


def parse_cube_from_json(json_data):
    return Cube(json_data['position']['x'], json_data['position']['y'], json_data['style_id'])


def parse_field_cubes_from_json(json_data):
    cubes = []

    for cube in json_data:
        floor_cube = parse_field_cube_from_json(cube)
        cubes.append(floor_cube)

    return cubes


def parse_field_cube_from_json(json_data):
    base_cube = parse_cube_from_json(json_data)
    return FieldCube(base_cube.position_x, base_cube.position_y, base_cube.style_id, json_data['is_solid'])


def parse_cube_styles_from_json(json_data):
    cube_styles = []

    for style in json_data:
        cube_styles.append(CubeStyle(style['id'], style['color'], style.get('texture_path')))

    return cube_styles
