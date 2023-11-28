""" template-maker.py: Builds templates found within a set of FPP files

Makes templates from FPP files. This is performed both on FPPs, included FPPs, and recursively through generated
templates. Templates are generated from stylized includes of the form:

```
include "<template base name>.<template instance name>.fppt"
```
Template inputs are of the form `<template base name>.fppt` found in any listed fprime library.


@copyright
Copyright 2022, by the California Institute of Technology.
ALL RIGHTS RESERVED.  United States Government Sponsorship
acknowledged.

@author mstarch
"""
import argparse
import itertools
import os
import shutil
import sys
import re

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import yaml
import jinja2


TEMPLATE_FOLDER_NAME = "topology-templates"
SNIPPETS_FOLDER_NAME = "snippets"
TEMPLATE_SUFFIX = ".fppt"


def template_information(template_invocation_path: Path, fprime_locations: List[str]) -> Tuple[Path, str, str]:
    """ Calculate path to template path, template base name, and template name based on template invocation """
    template_definition = f"{ Path(template_invocation_path.stem).stem }{ template_invocation_path.suffix }"
    template_name = Path(template_invocation_path.stem).suffix.lstrip(".")

    possible_locations = [Path(possible) / TEMPLATE_FOLDER_NAME / template_definition for possible in fprime_locations]
    template_locations = [possible for possible in possible_locations if possible.exists() and possible.is_file()]

    if not template_locations:
        string_locations = ','.join([str(location) for location in possible_locations])
        raise FileNotFoundError(f"No template found in any of: { string_locations }")

    if len(template_locations) > 1:
        string_locations = ','.join([str(location) for location in template_locations])
        raise FileNotFoundError(f"Multiple template definitions: { string_locations }")
    return template_locations[0], template_definition, template_name


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
    with open(path, "r") as file_handle:
        matches = [pat.match(line) for line in file_handle]
    matches = [match.group(1) for match in matches if match]

    # Determine this file's invocations and this file's normal includes
    invocations = [path.parent / match for match in matches if match.endswith(TEMPLATE_SUFFIX)]
    includes = [path.parent / match for match in matches if not match.endswith(TEMPLATE_SUFFIX)]

    # Calculate invocations hidden in includes
    recursive_invocations = [get_template_invocations(path, fprime_locations) for path in includes]

    # Return local invocations and everything found recursively
    return invocations + list(itertools.chain.from_iterable(recursive_invocations))


def manufacture_files(data: str, output_file: Path, base_template: Path) -> List[Path]:
    """ Write out necessary files for template """
    # Make sure the parent path exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    snippets_output = output_file.parent / SNIPPETS_FOLDER_NAME
    snippets_output.mkdir(parents=True, exist_ok=True)
    snippets_input = base_template.parent / SNIPPETS_FOLDER_NAME

    # Copy snippets to output snippets folder
    snippets = []
    for current, _, files in os.walk(snippets_input):
        input_directory = Path(current)
        output_directory = snippets_output / input_directory.relative_to(snippets_input)

        output_directory.mkdir(parents=True, exist_ok=True)
        for file in files:
            shutil.copy(input_directory / file, output_directory / file)
            snippets.append(input_directory / file)

    # Write template invocation file
    with open(output_file, "w") as file_handle:
        file_handle.write(data)
    return snippets


def build_templates(path: Path, locations: List[str], environment: jinja2.Environment, step: int, offset: int = 0,counts: Union[Dict[str, int], None] = None, config: Dict[str,Any] = None) -> List[Path]:
    """ Builds needed templates from input file """
    base_parameters = {} if config is None else {**config}
    counts = {} if counts is None else counts

    template_invocations = get_template_invocations(path, locations)

    local_template_files = []
    invocations = []
    snippets = []
    for invocation in template_invocations:
        template_path, template_definition, template_name = template_information(invocation, locations)
        template = environment.get_template(template_definition)

        counts[template_definition] = counts.get(template_definition, -1) + 1
        template_parameters = {
            "template_name": template_name,
            "template_index": counts[template_definition],
            "template_offset": offset,
            **base_parameters
        }
        offset += step

        rendered = template.render(**template_parameters)
        snippets.extend(manufacture_files(rendered, invocation, template_path))

        local_template_files.append(template_path)
        invocations.append(invocation)

    recursive_template_files = [
        build_templates(invocation, locations, environment, step, offset, counts, config=config)
        for invocation in invocations
    ]
    return local_template_files + snippets + list(itertools.chain.from_iterable(recursive_template_files))


def main(args: List[str]):
    """Main function"""
    parser = argparse.ArgumentParser(description="Template processing script")
    parser.add_argument("--fprime-locations", nargs="+", help="Locations of fprime packages/libraries")
    parser.add_argument("--topology-files", type=Path, nargs="+", help="Paths the the main topology files")
    parser.add_argument("--offset-multiple", type=lambda x: int(x, 0),
                        help="Offset multiple for each templated topology hunk")
    parser.add_argument("--config", type=Path, help="Path to YAML file used for configuration")
    args_ns = parser.parse_args(args)

    if not args_ns.config.is_file():
        print(f"[ERROR] {args_ns.config} is not a file.", file=sys.stderr)
        return 1

    try:
        # Mine out the passed in settings
        locations = args_ns.fprime_locations
        inputs = args_ns.topology_files
        offset = args_ns.offset_multiple

        with open(args_ns.config, 'r') as file_handle:
            config = yaml.safe_load(file_handle)


        # Build jinja templates
        environment = setup_environment(locations)
        template_sets = [build_templates(path, locations, environment, offset, config=config) for path in inputs]
        [print(template_file) for template_file in set(itertools.chain.from_iterable(template_sets))]
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
