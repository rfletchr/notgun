import nuke
import notgun.adapters


class NukeApplicationAdapter(notgun.adapters.ApplicationAdapter):
    def filepath(self) -> str | None:
        return nuke.scriptName()

    def modified(self) -> bool:
        return nuke.root().modified()

    def save(self):
        if not nuke.scriptName():
            raise notgun.adapters.NotSavedError("cannot save an un-named file")

        nuke.scriptSave()

    def save_as(self, filepath: str):
        nuke.scriptSaveAs(filepath)

    def open(self, filepath: str):
        nuke.scriptOpen(filepath)

    def new(self):
        nuke.scriptNew()
