import atexit
cleanup_routines = [ lambda : print("cleaning up") ]

def register_cleanup_routine( cr ):
    global cleanup_routine
    cleanup_routines.append( cr )

def cleanup():
    global cleanup_routines
    try:
        print(len(cleanup_routines))
        for f in cleanup_routines:
           f() 
    except:
        pass

atexit.register(cleanup)
