#! /usr/bin/env python3

import sys, os, subprocess, platform, distro, pickle
import urllib.request, shutil, argparse, json, re
from logger import err, warn, log, verbose_log
from util import strip, str_to_class, get_os, get_temp_dir, get_install_dir, get_file_dir, get_home_dir, get_package_manager_name, is_owner_for_dir
from dependency import dependency, installed_dependency, version
from package_manager import package_manager, import_package_managers
from build_system import build_system, import_build_systems
from source_builder import source_builder

class dependency_handler:
    comment_re = re.compile("#")
    tag_re     = re.compile("\[.*\]")
    dependencies      = list()
    tagged_deps       = dict()
    deps_dict         = dict()
    temp_dir          = get_temp_dir()
    prefix            = ""
    deps_filename     = "eosio.deps"
    installed_deps    = dict()
    check_only        = False
    
    def download_dependency_and_unpack( self, dep, use_bin ):
        log.log("Downloading "+dep.name)
        url = ""
        if use_bin:
            url = dep.bin_url
        else:
            url = dep.source_url
        base_name = os.path.basename(url)
        urllib.request.urlretrieve( url, self.temp_dir+"/"+base_name )
        shutil.unpack_archive( self.temp_dir+"/"+base_name, self.temp_dir+"/"+dep.name )

        log.log("Unpacked "+base_name)
        os.remove( self.temp_dir+"/"+base_name )

    def check_dependency( self, dep ):
        packman = str_to_class(get_package_manager_name())()
        res = packman.check_dependency( dep )
        if res == package_manager.installed:
            log.log("Dependency ("+dep.name+") found!")
            return True
        elif res == package_manager.not_installed:
            warn.log( "Dependency ("+dep.name+" : "+dep.version.to_string()+") not found!" )
            if (not packman.install_dependency( dep ) and not self.check_only):
                    ### fallback
                    self.download_dependency_and_unpack( dep, len(dep.bin_url) > 0 )
                    sb = source_builder()
                    sb.build( self.installed_deps, dep )
                    installed = sb.install( self.installed_deps, dep, self.prefix )
                    self.installed_deps[dep.name] = installed
            return False
        elif res == package_manager.not_satisfiable:
            if (not self.check_only):
                warn.log( "Dependency ("+dep.name+" : "+dep.version.to_string()+") not satisfiable, doing a source install!" )
                self.download_dependency_and_unpack( dep, len(dep.bin_url) > 0 )
                sb = source_builder()
                sb.build( self.installed_deps, dep )
                installed = sb.install( self.installed_deps, dep, self.prefix )
                self.installed_deps[dep.name] = installed
            else:
                warn.log( "Dependency ("+dep.name+" : "+dep.version.to_string()+") not satisfiable!" )
            return False
        else:
            err.log("Dependency ("+dep.name+") installed but version is too low ("+packman.get_version(dep).to_string()+")")
            return False

    def check_dependencies( self ):
        self.read_dependency_file( self.deps_filename )
        dep_check = True
        for dep in self.dependencies:
            log.log("Checking dep "+dep.name)
            if dep.name in self.installed_deps:
                log.log("Dependency ("+dep.name+") found!")
                continue
            if dep.is_executable():
                installed_dep = dep.find_executable()
                if installed_dep:
                    self.installed_deps[dep.name] = dep.find_executable()
                else:
                    dep_check = dep_check and self.check_dependency( dep )
            else:
                dep_check = dep_check and self.check_dependency( dep )
        return dep_check

    def write_installed_deps_file( self ):
        local_deps = dict()
        system_deps = dict()
        for k, v in installed_deps.items():
            if os.path.commonprefix(get_home_dir(), v.path) == get_home_dir():
                warn.log("Can install to "+get_home_dir())
        deps_file = open("__deps", "wb")
        pickle.dump( self.installed_deps, deps_file )
        deps_file.close()
    
    def read_installed_deps_file( self ):
        try:
            deps_file = open("__deps", "rb")
            self.installed_deps = pickle.load(deps_file)
            deps_file.close()
        except:
            pass

    def read_dependency_file( self, dep_fname ):
        dep_file = open( dep_fname, "r" )
        mode = 0
        tag_name = ""
        os_name, dist, ver = get_os()
        for line in dep_file:
            if self.comment_re.match(line) or not line or line == '\n':
                continue

            if self.tag_re.match(line):
                if (line.lstrip().rstrip()[1:-1] == "dependencies"):
                    mode = 1
                elif (strip(line)[1:-1] == "urls"):
                    mode = 3
                elif (strip(line)[1:-1] == "commands"):
                    mode = 4
                elif (strip(line)[1:-1] == "packages"):
                    mode = 5
                else:
                    tag_name = line.lstrip().rstrip()[1:-1]
                    if (tag_name not in self.tagged_deps):
                        self.tagged_deps[tag_name] = list()

                    mode = 2
                continue

            ### [dependencies]
            if mode == 1:
                dep_name = strip(line.split(":")[0])
                ds = strip(line.split(":")[1])[1:-1].split(",")
                is_strict = ds[0].startswith(">=")
                if ds[0] == "any":
                    vers = version(-1, -1)
                else:
                    vers = version(int(strip(ds[0].replace(">=", "")).split(".")[0]), int(strip(ds[0].replace(">=", "")).split(".")[1]))
                dep = dependency( dep_name, vers, strip(ds[1]), strip(ds[2]) )
                dep.strict = is_strict
                self.dependencies.append( dep )
                self.deps_dict[dep.name] = dep
            
            ### [tag]
            elif mode == 2:
                self.tagged_deps[tag_name].append(line.lstrip().rstrip())

            ### [urls]
            elif mode == 3:
                dep_name = strip(line.split(":", 1)[0])
                tmp = strip(strip(line.split(":", 1)[1])[1:-1])
                tag = strip(strip(tmp.split(":", 2)[0]))
                spec = strip(strip(tmp.split(":", 2)[1]))
                url = strip(strip(tmp.split(":", 2)[2]))
                if (tag == "source"):
                    if (spec == "all" or spec == dist+"<"+ver+">" or spec == dist):
                        self.deps_dict[dep_name].source_url = url
                elif (tag == "bin"):
                    if (spec == "all" or spec == dist+"<"+ver+">" or spec == dist):
                        self.deps_dict[dep_name].bin_url = url
                else:
                    err.log("Unsupported url type "+tag) 

            ### [commands]
            elif mode == 4:
                dep_name = strip(line.split(":", 1)[0])
                tmp = strip(strip(line.split(":", 1)[1])[1:-1])
                tag = strip(strip(tmp.split(":", 2)[0]))
                spec = strip(strip(tmp.split(":", 2)[1]))
                cmds = strip(strip(tmp.split(":", 2)[2]))
                if (tag == "pre_build"):
                    if (spec == "all" or spec == dist+"<"+ver+">" or spec == dist):
                        self.deps_dict[dep_name].pre_build_cmds = cmds
                elif (tag == "build"):
                    if (spec == "all" or spec == dist+"<"+ver+">" or spec == dist):
                        self.deps_dict[dep_name].build_cmds = cmds
                elif (tag == "install"):
                    if (spec == "all" or spec == dist+"<"+ver+">" or spec == dist):
                        self.deps_dict[dep_name].install_cmds = cmds
                else:
                    err.log("Unsupported command type "+tag) 

            ### [packages]
            elif mode == 5:
                dep_name = strip(line.split(":", 1)[0])
                tmp = strip(strip(line.split(":", 1)[1])[1:-1])
                for pair in tmp.split(","):
                    tag = strip(strip(pair.split(":", 1)[0]))
                    name = strip(strip(pair.split(":", 1)[1]))
                    if tag == "all":
                        self.deps_dict[dep_name].package_name = name
                    else:
                        if tag == dist+"<"+ver+">" or tag == dist:
                            self.deps_dict[dep_name].package_name = name
                            break
                        else:
                            continue

    def get_prefix(self, dep_name):
        if dep_name in self.installed_deps:
            return self.installed_deps[dep_name].path
        else:
            err.log("Dependency ("+dep_name+") not available")

    def check_if_uid_satisfied(self, pfx):
        self.prefix = os.path.abspath(os.path.realpath(os.path.expanduser(pfx)))
        if not is_owner_for_dir(self.prefix):
            err.log("Prefix for installation <"+self.prefix+"> needs root access, use sudo")

    def __init__(self, pfx):
        import_package_managers()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manager for dependencies")
    parser.add_argument('--verbose', dest='verbose', action="store_true", default=False)
    parser.add_argument('--prefix', type=str, dest='prefix', default="/usr/local")
    parser.add_argument('--query', type=str, dest='query', default="")
    parser.add_argument('--path', type=str, dest='path', default="")
    parser.add_argument('--check', dest='check', action='store_true', default=False)
    parser.add_argument('file', type=str, nargs='?')

    args = parser.parse_args()
    handler = dependency_handler( args.prefix )
    handler.read_installed_deps_file()
    if args.verbose:
        verbose_log.silence = False
    if args.file:
        handler.deps_filename = args.file
    if args.check:
        handler.check_only = True
        if not handler.check_dependencies():
            exit(-1)
        exit(0)
    if args.query:
        log.log("Prefix for "+args.query+" : "+handler.get_prefix(args.query))
        exit(0)
    handler.check_if_uid_satisfied( args.prefix )
    handler.check_dependencies()
    handler.write_installed_deps_file()
    exit(0)
    try:
        handler = dependency_handler( args.prefix )
        handler.read_installed_deps_file()
        if args.query:
            log.log("Prefix for "+args.query+" : "+handler.get_prefix(args.query))
            exit(0)
        handler.check_if_uid_satisfied( args.prefix )
        handler.check_dependencies()
        handler.write_installed_deps_file()
    except Exception as ex:
        warn.log(str(ex))
        err.log("Critical failure")
