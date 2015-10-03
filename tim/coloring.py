import colorama as cr
cr.init()

class TimColorer(object):

    def __init__(self, use_color):
        """TODO: to be defined1. """

        self.use_color = use_color

    def red(self, str):
        if self.use_color:
            return cr.Fore.RED + str + cr.Fore.RESET
        else:
            return str

    def green(self, str):
        if self.use_color:
            return cr.Fore.GREEN + str + cr.Fore.RESET
        else: 
            return str

    def yellow(self, str):
        if self.use_color: 
            return cr.Fore.YELLOW + str + cr.Fore.RESET
        else:
            return str

    def blue(self, str):
        if self.use_color: 
            return cr.Back.WHITE + cr.Fore.BLUE + str + cr.Fore.RESET + cr.Back.RESET
        else:
            return str

    def bold(self, str):
#doesn't do much on my ConEmu Windows 7 system, but let's see
        if self.use_color:
            return cr.Style.BRIGHT + str + cr.Style.RESET_ALL
        else:
            return str

