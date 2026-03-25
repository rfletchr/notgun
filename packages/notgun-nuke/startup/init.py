import nuke
import notgun.bootstrap
import notgun_nuke.adapters


from PySide6 import QtCore, QtWidgets


class DefferredInstructionHandler(QtCore.QObject):
    def __init__(self, instruction: notgun.bootstrap.InstructionTypes, parent=None):
        super().__init__(parent)
        self.instruction = instruction
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.handle_instruction)

    def start(self, delay_ms=1000):
        self.timer.start(delay_ms)

    def handle_instruction(self):
        print(f"Handling instruction: {self.instruction}")
        if isinstance(self.instruction, notgun.bootstrap.NewFileInstruction):
            nuke.scriptSaveAs(self.instruction.filepath)

        if isinstance(self.instruction, notgun.bootstrap.OpenFileInstruction):
            nuke.scriptClear()
            nuke.scriptOpen(self.instruction.filepath)


if notgun.bootstrap.BootstrapData.is_in_env():
    print("Bootstrap data found in environment, initializing project...")
    bootstrap = notgun.bootstrap.BootstrapData.from_env()
    bootstrap.clear_env()

    project = notgun.bootstrap.init(bootstrap, make_current=True)
    project.set_app(notgun_nuke.adapters.NukeApplicationAdapter())

    handler = DefferredInstructionHandler(bootstrap.instruction)

    setattr(nuke, "_notgun_deferred_instruction_handler", handler)
    handler.start()
