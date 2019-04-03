from package_manager import package_manager
from util import execute_cmd
from dependency import version
from logger import err, warn, log

class brew(package_manager):
    def get_version(self, dep):
        eo, ee, ec = execute_cmd("brew info "+dep.package_name)
        if (eo and ec == 0):
            vers_str = eo.split()[2]
            ver = version(int(self.strip_suff(vers_str.split(".")[0])), int(self.strip_suff(vers_str.split(".")[1])))
            return ver
        return None

    def check_dependency(self, dep):
        vers = self.get_version(dep)
        eo, ee, ec = execute_cmd("brew list --versions "+dep.package_name)
        ### installed
        if eo and ec == 0:
            if vers.ge(dep.version):
                return self.installed
            else:
                return self.installed_wrong
        else:
            if dep.strict:
                if vers.eq(dep.version):
                    return self.not_installed
            else: 
                if vers.ge(dep.version):
                    return self.not_installed
            return self.not_satisfiable
    def install_dependency(self, dep):
        log.log("Installing "+dep.name+" "+dep.package_name)
        eo, ee, ec = execute_cmd("brew install "+dep.package_name)
        return eo and ec == 0
