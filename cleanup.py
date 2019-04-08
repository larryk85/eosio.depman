import atexit

def null_func():
    pass

cleanup_routines = [ null_func ]

def register_cleanup_routine( cr ):
    global cleanup_routine
    cleanup_routines.append( cr )

def cleanup():
    global cleanup_routines
    try:
        for f in cleanup_routines:
           f() 
    except:
        pass

atexit.register(cleanup)
