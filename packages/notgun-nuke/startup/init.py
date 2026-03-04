import notgun.bootstrap
import notgun_nuke.adapters

pipeline = notgun.bootstrap.init_from_env()
pipeline.set_app(notgun_nuke.adapters.NukeApplicationAdapter())
