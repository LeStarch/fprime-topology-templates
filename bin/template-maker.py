
import argparse
import itertools
import sys
import re

from pathlib import Path
from typing import List, Tuple, Union

import jinja2


TEMPLATE_FOLDER_NAME = "topology-templates"
TEMPLATE_SUFFIX = "fppt"


def template_information(template_invocation_path: Path, fprime_locations: Union[List[str], None] = None) -> Tuple[Path, str, str]:
    """ Calculate path to template path, template base name, and template name based on template invocation """
    template_definition = f"{ Path(template_invocation_path.stem).stem }.{ template_invocation_path.suffix }"
    possible_locations = [Path(possible) / TEMPLATE_FOLDER_NAME / template_definition for possible in fprime_locations]
    template_locations = [possible for possible in possible_locations if possible.exists() and possible.is_file()]

    if fprime_locations is not None and not template_locations:
        string_locations = ','.join([str(location) for location in possible_locations])
        raise FileNotFoundError(f"No template found in any of: { string_locations }")

    if fprime_locations is not None and len(template_locations) > 1:
        string_locations = ','.join([str(location) for location in template_locations])
        raise FileNotFoundError(f"Multiple template definitions: { string_locations }")
    return None if fprime_locations is None else template_locations[0], template_definition, Path(template_invocation_path.stem).suffix


def setup_environment(fprime_locations: List[str]) -> jinja2.Environment:
    """ Creates a Jinja2 environment from a list of template directories """
    possible_locations = [Path(location) / TEMPLATE_FOLDER_NAME for location in fprime_locations]
    template_locations = [location for location in possible_locations if location.exists() and location.is_dir()]

    if not template_locations:
        string_locations = ','.join([str(location) for location in possible_locations])
        raise FileNotFoundError(f"No template directories found in any of: { string_locations }")

    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=template_locations, followlinks=True),
        autoescape=False
    )
    return environment


def get_template_invocations(path: Path, fprime_locations: List[str], pat: re.Pattern = re.compile(" *include +['\"]([^'\"]+)['\"]")) -> List[Path]:
    """ Calculate template invocations contained within supplied file """

    # Find all include matches in this file
    with open(path) as file_handle:
        matches = [pat.match(line) for line in file_handle]
    matches = [match.group(1) for match in matches if match]

    # Determine this file's invocations and this file's normal includes
    match_file_suffix = f".{ TEMPLATE_SUFFIX }"
    invocations = [path / match for match in matches if match.endswith(match_file_suffix)]
    includes = [path / match for match in matches if not match.endswith(match_file_suffix)]

    # Calculate recursive invocations by looking at the base template for invocations and include file for includes
    template_infos = [template_information(invocation, fprime_locations) for invocation in invocations]
    base_templates = [template for template, _, _ in template_infos]
    recursive_invocations = [get_template_invocations(path, fprime_locations) for path in base_templates + includes]

    # Return local invocations and everything found recursively
    return invocations + list(itertools.chain(*recursive_invocations))


def build_templates(template_invocations: List[Path], environment: jinja2.Environment, template_offset_multiple: int):
    """ Builds needed templates from list of templates """
    base_parameters = {}  # TODO: fill with configurable parameters
    instance_counts = {}
    template_offset = 0

    for invocation in template_invocations:
        _, template_definition, template_name = template_information(invocation)
        template = environment.get_template(template_definition)

        instance_counts[template_definition] = instance_counts.get(template_definition, -1) + 1
        template_parameters = {
            "template_name": template_name,
            "template_index": instance_counts[template_definition],
            "template_offset": template_offset,
            **base_parameters
        }
        template_offset += template_offset_multiple

        rendered = template.render(**template_parameters)
        with open(invocation, "w") as file_handle:
            file_handle.write(rendered)


def main(args: List[str]):
    """Main function"""
    parser = argparse.ArgumentParser(description="Template processing script")
    parser.add_argument("--fprime-locations", nargs="+", help="Locations of fprime packages/libraries")
    parser.add_argument("--topology-files", type=Path, nargs="+", help="Paths the the main topology files")
    parser.add_argument("--offset-multiple", type=int, help="Offset multiple for each templated topology hunk")
    args_ns = parser.parse_args(args)

    try:
        environment = setup_environment(args_ns.fprime_locations)
        file_invocations = [get_template_invocations(path, args_ns.fprime_locations) for path in args_ns.topology_files]
        invocations = list(itertools.chain(*file_invocations))
        build_templates(invocations, environment, args_ns.offset_multiple)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
