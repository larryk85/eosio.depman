from logger import err, warn, log
from util import execute_cmd_dump_output, get_temp_dir
from build_system import build_system

### concrete implementation for autoconf
class autoconf(build_system):
    def pre_build(self, dep):
        log.log("autoconf : pre-build step for "+dep.name)
        return execute_cmd_dump_output("../configure --prefix="+get_temp_dir()+"/"+dep.name+".tmp "+dep.pre_build_cmds)

    def build(self, dep):
        log.log("autoconf : build step for "+dep.name)
        return execute_cmd_dump_output("make -j "+dep.build_cmds)

    def install(self, dep):
        log.log("autoconf : install step for "+dep.name)
        return execute_cmd_dump_output("make install "+dep.install_cmds)