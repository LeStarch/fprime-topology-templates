####
# templates.cmake:
#
# Topology template support.  Calls `template-maker.py` when invoked in `make_templates(...)`. This must happen before
# any calls to `register_fprime_...` functions
#
# Copyright 2022, by the California Institute of Technology.
# ALL RIGHTS RESERVED.  United States Government Sponsorship
# acknowledged.
####
include(utilities)
set(TEMPLATES_EXECUTABLE_PATH "${CMAKE_CURRENT_LIST_DIR}/../bin/template-maker.py")

####
# make_templates: make templates inline
#
# - TEMPLATE_SOURCE_FILES: list of FPP input files
# - OFFSET_MULTIPLE: multiple of base id steps in templates
#####
function(make_templates TEMPLATE_SOURCE_FILES OFFSET_MULTIPLE TEMPLATE_CONFIG)
    set(EXECUTE_ARGUMENTS
        ${PYTHON} ${TEMPLATES_EXECUTABLE_PATH}
        "--fprime-locations" ${FPRIME_BUILD_LOCATIONS}
        "--topology-files" ${TEMPLATE_SOURCE_FILES}
        "--offset-multiple" "${OFFSET_MULTIPLE}"
        "--config" "${TEMPLATE_CONFIG}"
    )
    # Execute the process
    execute_process_or_fail(
        "Failed to run template generation"
        ${EXECUTE_ARGUMENTS}
        OUTPUT_VARIABLE FILE_LISTING
    )
    # Mark files as templates
    string(REPLACE "\n" ";" FILE_LISTING "${FILE_LISTING}")
    foreach(FILE_ITEM IN LISTS FILE_LISTING)
        set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${FILE_ITEM}")
    endforeach()
endfunction(make_templates)
