cmake_minimum_required( VERSION 3.5 )

macro (find_depman Var)
   find_file(Var "eosio.depman" PATHS ${CMAKE_MODULE_PATH}/../)
endmacro()

macro (check_dependencies dep_file)
   find_file(DepMan "eosio.depman" PATHS ${CMAKE_MODULE_PATH}/../)
   message(STATUS "DPE ${DepMan}")
   execute_process(COMMAND "${DepMan}" "${dep_file}" "--check"
      RESULT_VARIABLE    cmd_res
      ERROR_VARIABLE     cmd_error
      OUTPUT_VARIABLE    cmd_output)
   if (${cmd_res} STREQUAL "0")
      message(STATUS "Dependency checking passed : ${cmd_output}")
   else()
      message(WARNING "Dependency checking failed : ${cmd_output}")
   endif()
endmacro()

macro (get_dependency_prefix dep_file dep_name)
   find_file(DepMan "eosio.depman" PATHS ${CMAKE_MODULE_PATH}/../)
   execute_process(COMMAND "${DepMan}" "dep_file" "--query ${dep_name}"
      RESULT_VARIABLE cmd_res
      ERROR_FILE      cmd_error
      OUTPUT_FILE     cmd_output)
endmacro()
