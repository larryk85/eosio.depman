from package_manager import package_manager
from util import execute_cmd
from dependency import version

class brew(package_manager):
    def get_version(self, dep):
        print(dep.package_name)
        eo, ee, ec = execute_cmd("brew info "+dep.package_name)
        print("Get version")
        print(eo)
        if (eo and ec == 0):
            vers_str = eo.split()[2]
            return version(int(self.strip_suff(vers_str.split(".")[0])), int(self.strip_suff(vers_str.split(".")[1])))
        return None

    def check_dependency(self, dep):
        vers = self.get_version(dep)
        print("Herr")
        eo, ee, ec = execute_cmd("brew list --versions "+dep.package_name)
        ### installed
        if eo and ec == 0:
            if vers.ge(dep.version):
                return self.installed
            else:
                return self.installed_wrong
        else:
            if vers.ge(dep.version):
                return self.not_installed
            else:
                return self.not_satisfiable
    def install_dependency(self, dep):
        log.log("Installing "+dep.name+" "+dep.package_name)
        #eo, ee, ec = execute_cmd("brew install "+dep.package_name)
        #return eo and ec == 0
        return True
