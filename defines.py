from PyQt5.QtCore import Qt


class Data:
    def __init__(self, r = 0, c = 0):
        # these are needed on commands undo
        self.r = r
        self.c = c

    def is_data(self):
        return False

    def is_at(self, index):
        return self.r == index.row() and self.c == index.column()


class NoteData(Data):
    def __init__(self, r = 0, c = 0, content = ''):
        super().__init__(r, c)
        self.content = content

    def is_data(self):
        return True


class StyledNoteData(NoteData):
    def __init__(self, r = 0, c = 0, content = '', bgcolor = None):
        super().__init__(r, c, content)
        self.bgcolor = bgcolor


class Checker:
    class Def:
        def __init__(self, checker_str, bgcolor, fgcolor=None):
            self.str = checker_str
            self.bgcolor = bgcolor
            self.fgcolor = fgcolor

    IGNORE = Def('-', Qt.yellow)
    PROGRESS = Def('>', Qt.blue, Qt.white)
    DONE = Def('o', Qt.green)
    MISSED = Def('x', Qt.red, Qt.white)
    MOVETO = Def('m>', Qt.darkCyan, Qt.white)
    MOVEFROM = Def('<m', Qt.cyan)

    @staticmethod
    def get_def(checker_str):
        if Checker.IGNORE.str == checker_str:
            return Checker.IGNORE
        elif Checker.PROGRESS.str == checker_str:
            return Checker.PROGRESS
        elif Checker.DONE.str == checker_str:
            return Checker.DONE
        elif Checker.MISSED.str == checker_str:
            return Checker.MISSED
        elif Checker.MOVETO.str == checker_str:
            return Checker.MOVETO
        elif Checker.MOVEFROM.str == checker_str:
            return Checker.MOVEFROM
        else:
            return None
