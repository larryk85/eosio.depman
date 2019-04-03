import os, shutil, json, pickle
from logger import err, warn, log
from cleanup import register_cleanup_routine
from util import str_to_class, get_temp_dir
from dependency import dependency, installed_dependency, version, serialize
from build_system import build_system, noop_build_system, import_build_systems

class source_builder:
    def __init__(self):
        import_build_systems()
    
    def check_install(self, installed_files):
        for f in installed_files:
            if os.path.isfile(f):
                return True
        return False
        
    def build(self, dep):
        old_cwd = os.getcwd()
        tmpd = get_temp_dir()+"/"+dep.name
        register_cleanup_routine( lambda : shutil.rmtree(tmpd) )
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
            err.log("Pre-build stage for "+dep.name+" failed!")
        if not builder.build(dep):
            err.log("Build stage for "+dep.name+" failed!")

        os.chdir( old_cwd )
    
    def install(self, dep, prefix):
        old_cwd = os.getcwd()
        tmpd = get_temp_dir()+"/"+dep.name
        register_cleanup_routine( lambda : shutil.rmtree(tmpd) )
        register_cleanup_routine( lambda : shutil.rmtree(tmpd+".tmp") )
        full_dir = tmpd+"/"+os.listdir(tmpd)[0]+"/build"
        os.chdir( full_dir )
        builder = str_to_class(dep.build_sys)()
        if not builder.install(dep):
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

        ### check whether currently installed
        if self.check_install(filenames):
            err.log("Dependency "+dep.name+" is already installed at location "+prefix)

        for i in range(0, len(filenames)):
            try:
                os.makedirs( os.path.dirname( filenames[i] ) )
            except:
                pass
            ### install to the prefix
            shutil.move( old_filenames[i], filenames[i] )
        return installed_dependency( dep, True, prefix, filenames ) 
