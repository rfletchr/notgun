name = "notgun_nuke"
version = "0.1.0"
requires = ["notgun", "nuke"]
build_requires = ["python"]


def commands():
    env.NUKE_PATH.prepend("{root}/startup")
