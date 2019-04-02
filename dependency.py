class dependency:
    def __init__(self, nm, vs, pn, bs, su, bu, pbc, bc, ic):
        self.name         = nm
        self.version      = vs
        self.build_sys    = bs
        self.source_url   = su
        self.package_name = pn
        self.bin_url      = bu
        self.pre_build_cmds = pbc
        self.build_cmds   = bc
        self.install_cmds = ic

    def __init__(self, nm, vs, bs):
        self.name         = nm
        self.version      = vs
        self.build_sys    = bs

    name             = ""
    package_name     = ""
    version          = ""
    build_sys        = ""
    source_url       = ""
    bin_url          = ""
    build_cmds       = ""
    pre_build_cmds   = ""
    install_cmds     = ""

class installed_dependency:
    def __init__(self, p, fs):
        path = p
        files = fs

    path  = ""
    files = list()

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
