#! /usr/local/bin/python3

import sys, os, subprocess, platform, distro
import tarfile, zipfile 
import urllib.request, shutil, argparse, json, re
from logger import err, warn, log
from util import execute_cmd, execute_cmd_dump_output, strip, str_to_class, get_os, get_temp_dir, get_install_dir, get_file_dir, get_package_manager_name
from dependency import dependency, installed_dependency, version
from package_manager import package_manager, import_package_managers

### interface for build systems
class build_system:
    def pre_build(self, dep, cmds):
        pass
    def build(self, dep, cmds):
        pass
    def install(self, dep, cmds):
        pass

### implementation for pre-built sources
class noop_build_system:
    def pre_build(self, dep, cmds):
        pass
    def build(self, dep, cmds):
        pass
    def install(self, dep, cmds):
        log.log("install step for "+dep.name)

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

class source_builder:
    def build(self, dep):
        old_cwd = os.getcwd()
        tmpd = get_temp_dir()+"/"+dep.name
        full_dir = tmpd+"/"+os.listdir(tmpd)[0]
        os.chdir( full_dir )
        try:
            os.mkdir( full_dir+"/build" )
        except:
            pass
        os.chdir( "./build" )
        builder = None
        if len(dep.bin_url) > 0:
            builder = noop_build_system()
        else:
            builder = str_to_class(dep.build_sys)()
        
        if not builder.pre_build(dep):
            shutil.rmtree(tmpd)
            err.log("Pre-build stage for "+dep.name+" failed!")
        if not builder.build(dep):
            shutil.rmtree(tmpd)
            err.log("Build stage for "+dep.name+" failed!")

        os.chdir( old_cwd )
        return lambda : shutil.rmtree(tmpd)
    
    def install(self, dep, prefix):
        tmpd = get_temp_dir()+"/"+dep.name
        old_cwd = os.getcwd()
        tmpd = get_temp_dir()+"/"+dep.name
        full_dir = tmpd+"/"+os.listdir(tmpd)[0]+"/build"
        os.chdir( full_dir )
        builder = str_to_class(dep.build_sys)()
        if not builder.install(dep):
            shutil.rmtree(tmpd)
            shutil.rmtree(get_temp_dir()+"/"+dep.name)
            err.log("Install stage for "+dep.name+" failed!")
        os.chdir( old_cwd )
        filenames = list()
        old_filenames = list()
        for path, subdirs, files in os.walk(tmpd+".tmp"):
            for fn in files:
                full_path = os.path.join(path, fn)
                rel_path  = os.path.relpath(full_path, tmpd+".tmp")
                fixed_path = os.path.join(prefix, rel_path)
                filenames.append(fixed_path)
                old_filenames.append(full_path)
        
        ### for now ignore errors when making the prefix folder
        try:
            os.makedirs( prefix )
        except:
            pass

        installed_dep = installed_dependency( prefix, filenames )
        for i in range(0, len(filenames)):
            try:
                os.makedirs( os.path.dirname( filenames[i] ) )
            except:
                pass
            ### install to the prefix
            shutil.move( old_filenames[i], filenames[i] )
        return lambda : shutil.rmtree(tmpd+".tmp")

class dependency_handler:
    comment_re = re.compile("#")
    tag_re     = re.compile("\[.*\]")
    
    dependencies  = list()
    tagged_deps   = dict()
    deps_dict     = dict()
    temp_dir      = get_temp_dir()
    prefix        = ""
    deps_filename = "eosio.deps"

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

    def check_dependencies( self ):
        packman = str_to_class(get_package_manager_name())()
        print (packman)

        self.read_dependency_file( self.deps_filename )

        for dep in self.dependencies:
            print("Checking dep "+dep.name)
            res = packman.check_dependency( dep )
            if res == package_manager.installed:
                log.log("Dependency ("+dep.name+") found!")
            elif res == package_manager.not_installed:
                warn.log( "Dependency ("+dep.name+" : "+dep.version.to_string()+") not found!" )
                if (not packman.install_dependency( dep )):
                        ### fallback
                        self.download_dependency_and_unpack( dep, len(dep.bin_url) > 0 )
                        sb = source_builder()
                        cleanup_build   = sb.build( dep )
                        cleanup_install = sb.install( dep, self.prefix )
                        cleanup_build()
                        cleanup_install()
            elif res == package_manager.not_satisfiable:
                warn.log( "Dependency ("+dep.name+" : "+dep.version.to_string()+") not satisfiable, doing a source install!" )
                self.download_dependency_and_unpack( dep, len(dep.bin_url) > 0 )
                sb = source_builder()
                cleanup_build   = sb.build( dep )
                cleanup_install = sb.install( dep, self.prefix )
                cleanup_build()
                cleanup_install()

            else:
                err.log("Dependency ("+dep.name+") installed but version is too low ("+packman.get_version(dep).to_string()+")")

    def read_dependency_file( self, dep_fname ):
        print(get_os()[0])
        print(get_os()[1])
        print(get_os()[2])
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
                vers = version(int(strip(ds[0]).split(".")[0]), int(strip(ds[0]).split(".")[1]))
                dep = dependency( dep_name, vers, strip(ds[1]) )
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


    def __init__(self, pfx):
        import_package_managers()
        self.prefix = os.path.abspath(os.path.realpath(os.path.expanduser(pfx)))
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manager for dependencies")
    parser.add_argument('--prefix', type=str, dest='prefix', default="/usr/local")
    args = parser.parse_args()
    handler = dependency_handler( args.prefix )
    handler.check_dependencies()

#    try:
#        handler = dependency_handler()
#        handler.check_dependencies()
#    except:
#        err.log("Critical failure")
