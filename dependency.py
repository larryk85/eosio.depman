import os
from json import JSONEncoder, JSONDecoder, dumps
from util import execute_cmd_dump_output

class dependency_encoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

def serialize( installed_dep ):
    return dumps(installed_dep, cls=dependency_encoder)

def from_json( jo ):
    return installed_dependency( jo["dep"], jo["provided"], jo["path"], jo["files"])

def deserialize( js ):
    return JSONDecoder(object_hook = from_json).decode(js)

class dependency:
    def __init__(self, nm, vs, st, pn, en, bs, su, bu, pbc, bc, ic):
        self.name         = nm
        self.version      = vs
        self.strict       = st
        self.build_sys    = bs
        self.source_url   = su
        self.package_name = pn
        self.exe_name     = en
        self.bin_url      = bu
        self.pre_build_cmds = pbc
        self.build_cmds   = bc
        self.install_cmds = ic

    def __init__(self, nm, vs, bs):
        self.name         = nm
        self.version      = vs
        self.build_sys    = bs

    name             = "***"
    package_name     = "***"
    exe_name         = "***"
    strict           = False
    version          = ""
    build_sys        = ""
    source_url       = ""
    bin_url          = ""
    build_cmds       = ""
    pre_build_cmds   = ""
    install_cmds     = ""

class installed_dependency:
    def __init__(self, d, prov, p, fs):
        self.dep      = d
        self.provided = prov
        self.path     = p
        self.files    = fs
    
    def execute(self, *cmds):
        cmd_str = ""
        for cmd in cmds:
            cmd_str += " "+cmd
        eo, ee, ec = execute_cmd_dump_output(os.join(path, dep.name), cmd_str)
        return ec == 0

    dep      = None
    provided = False
    path     = ""
    files    = list()

class version:
    def __init__(self, major, minor, patch):
        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)

    def __init__(self, major, minor):
        self.major = int(major)
        self.minor = int(minor)

    def ge(self, v):
        return self.major >= v.major and self.minor >= v.minor

    def eq(self, v):
        return self.major == v.major and self.minor == v.minor

    def to_string(self):
        return str(self.major)+"."+str(self.minor)

    major = 0
    minor = 0
    patch = -1
