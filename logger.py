import cleanup
class logger:
    red = "91;1"
    green = "92"
    yellow = "93;1"
    should_exit = False
    color = ""

    def __init__(self, c, se):
        self.color = c
        self.should_exit = se
        
    def log(self, s):
        print("\33["+self.color+"m"+s+"\33[0m")
        if self.should_exit:
            cleanup.cleanup()
            exit(-1)

log  = logger(logger.green, False)
warn = logger(logger.yellow, False)
err  = logger(logger.red, True)
