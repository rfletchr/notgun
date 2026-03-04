name = "notgun_launcher"
version = "0.1.0"
requires = ["python-3+", "notgun", "QtPy", "PySide6", "QtAwesome"]
build_requires = ["python"]


def commands():
    env.PYTHONPATH.prepend("{root}/src")
    env.PATH.prepend("{root}/bin")
