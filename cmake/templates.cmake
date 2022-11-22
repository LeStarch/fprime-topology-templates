
set(TEMPLATES_EXECUTABLE_PATH "${CMAKE_CURRENT_LIST_DIR}/../bin/templates-maker.py")

function(make_templates OFFSET_MULTIPLE TEMPLATE_SOURCE_FILE)
    execute_process(
        COMMAND ${PYTHON} ${TEMPLATES_EXECUTABLE_PATH}
            "--fprime-locations" ${FPRIME_BUILD_LOCATIONS}
            "--topology-files" ${TEMPLATE_SOURCE_FILE}
            "--offset-multiple" "${OFFSET_MULTIPLE}"
    )
endfunction(make_templates)