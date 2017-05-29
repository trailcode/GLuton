from PyQt4.QtGui import QFont
from spyderlib.widgets.internalshell import InternalShell
from spyderlib.utils.module_completion import module_completion

class SpyderConsoleWidget(InternalShell):
    def __init__(self, context=None):
        my_locals = {
            'context': context
        }
        super(SpyderConsoleWidget, self).__init__(namespace=my_locals)
        self.setObjectName('SpyderConsoleWidget')
        self.set_pythonshell_font(QFont('Mono'))
        self.interpreter.restore_stds()

    def get_module_completion(self, objtxt):
        """Return module completion list associated to object name"""
        return module_completion(objtxt)

    def run_command(self, *args):
        self.interpreter.redirect_stds()
        super(SpyderConsoleWidget, self).run_command(*args)
        self.flush()
        self.interpreter.restore_stds()

    def shutdown(self):
        self.exit_interpreter()