name = "notgun"
version = "0.1.0"
requires = ["python-3+", "requests", "shotgun_api3", "QtPy"]
build_requires = ["python"]


def commands():
    env.PYTHONPATH.prepend("{root}/src")
    env.PATH.prepend("{root}/bin")
