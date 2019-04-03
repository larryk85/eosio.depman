import atexit
cleanup_routine = lambda _ : print("Cleaning up")

def register_cleanup_routine( cr ):
    global cleanup_routine
    prev = cleanup_routine
    new = lambda _ : cr()
    cleanup_routine = lambda _ : prev(new())

def cleanup():
    try:
        cleanup_routine(None)
    except:
        pass

atexit.register(cleanup)
