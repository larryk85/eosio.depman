from logger import err, warn, log
from util import execute_cmd_dump_output
from build_system import build_system

### concrete implementation for bjam
class bjam(build_system):
    def pre_build(self, dep):
        log.log("bjam : pre-build step for "+dep.name)
        return execute_cmd_dump_output("../bootstrap.sh --prefix="+get_temp_dir()+"/"+dep.name+".tmp "+dep.pre_build_cmds)

    def build(self, dep):
        log.log("bjam : build step for "+dep.name)
        return execute_cmd_dump_output("../b2 -j "+dep.build_cmds)

    def install(self, dep):
        log.log("bjam : install step for "+dep.name)
        return execute_cmd_dump_output("../b2 install "+dep.install_cmds)
