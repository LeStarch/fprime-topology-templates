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
set(TEMPLATES_EXECUTABLE_PATH "${CMAKE_CURRENT_LIST_DIR}/../bin/template-maker.py")

####
# make_templates: make templates inline
#
# - TEMPLATE_SOURCE_FILES: list of FPP input files
# - OFFSET_MULTIPLE: multiple of base id steps in templates
#####
function(make_templates TEMPLATE_SOURCE_FILES OFFSET_MULTIPLE)
    set(EXECUTE_ARGUMENTS
        ${PYTHON} ${TEMPLATES_EXECUTABLE_PATH}
        "--fprime-locations" ${FPRIME_BUILD_LOCATIONS}
        "--topology-files" ${TEMPLATE_SOURCE_FILES}
        "--offset-multiple" "${OFFSET_MULTIPLE}"
    )
    # Print out output
    if (CMAKE_DEBUG_OUTPUT)
        string(REPLACE ";" " " EXECUTE_STRING "${EXECUTE_ARGUMENTS}")
        message(STATUS "Template Generation: ${EXECUTE_STRING}")
    endif()
    # Execute the process
    execute_process(COMMAND ${EXECUTE_ARGUMENTS}
        OUTPUT_VARIABLE FILE_LISTING
        RESULT_VARIABLE RESULT_CODE
    )
    # Check result
    if (NOT RESULT_CODE EQUAL 0)
        message(FATAL_ERROR "Failed to run template generation.")
    endif()
    # Mark files as templates
    string(REPLACE "\n" ";" FILE_LISTING "${FILE_LISTING}")
    foreach(FILE_ITEM IN LISTS FILE_LISTING)
        set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${FILE_ITEM}")
    endforeach()
endfunction(make_templates)