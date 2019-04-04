import os, sys
import cleanup
class logger:
    red    = "91;1"
    green  = "92"
    yellow = "93;1"
    blue   = "94;1"
    should_exit = False
    silence     = False
    color = ""

    def __init__(self, c, silence, se):
        self.color = c
        self.silence = silence
        self.should_exit = se
        
    def log(self, s):
        if not self.silence:
            print("\33["+self.color+"m"+s+"\33[0m")
            #if os.fstat(sys.stdout.fileno()).st_mode == 4096: # if we are not piping to a file
            #    print("\33["+self.color+"m"+s+"\33[0m")
            #else:
            #    print(s)
        if self.should_exit:
            cleanup.cleanup()
            exit(-1)

log          = logger(logger.green, False, False)
verbose_log  = logger(logger.blue, True, False)
warn         = logger(logger.yellow, False, False)
err          = logger(logger.red, False, True)
