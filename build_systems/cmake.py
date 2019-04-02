from logger import err, warn, log
from util import execute_cmd_dump_output
from package_manager import package_manager, import_package_managers
from build_system import build_system

### concrete implementation for autoconf
class cmake(build_system):
    def pre_build(self, dep):
        log.log("cmake : pre-build step for "+dep.name)
        return execute_cmd_dump_output("cmake .. -DCMAKE_INSTALL_PREFIX="+get_temp_dir()+"/"+dep.name+".tmp "+dep.pre_build_cmds)

    def build(self, dep):
        log.log("cmake : build step for "+dep.name)
        return execute_cmd_dump_output("make -j "+dep.build_cmds)

    def install(self, dep):
        log.log("cmake : install step for "+dep.name)
        return execute_cmd_dump_output("make install "+dep.install_cmds)
