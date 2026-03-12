import notgun.bootstrap
import notgun_nuke.adapters

bootstrap = notgun.bootstrap.BootstrapData.from_env()
project = notgun.bootstrap.init(bootstrap, make_current=True)
project.set_app(notgun_nuke.adapters.NukeApplicationAdapter())

if isinstance(bootstrap.instruction, notgun.bootstrap.NewFileInstruction):
    project.app().save_as(bootstrap.instruction.filepath)

if isinstance(bootstrap.instruction, notgun.bootstrap.OpenFileInstruction):
    project.app().save_as(bootstrap.instruction.filepath)
