name = "notgun_nuke"
version = "0.1.1"
requires = ["notgun", "nuke"]
build_requires = ["python"]


def commands():
    env.NUKE_PATH.prepend("{root}/startup")
    env.PYTHONPATH.prepend("{root}/src")
