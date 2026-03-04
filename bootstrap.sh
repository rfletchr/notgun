# rez bind python -r --exe $(which python3)
rez pip --install qtpy
rez pip --install qtawesome
rez pip --install PySide6
rez pip --install requests
rez pip --install git+https://github.com/shotgunsoftware/python-api.git
(cd packages/notgun && rez build -i)
(cd packages/notgun-launcher && rez build -i)
(cd packages/notgun-nuke && rez build -i)