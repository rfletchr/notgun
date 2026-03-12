import notgun.bootstrap
import notgun_nuke.adapters

project = notgun.bootstrap.init_from_env()
project.set_app(notgun_nuke.adapters.NukeApplicationAdapter())
