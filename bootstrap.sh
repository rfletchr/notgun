rez bind python -r --exe $(which python3)
rez pip -r --install qtpy
rez pip -r --install qtawesome
rez pip -r --install PySide6
rez pip -r --install requests
rez pip -r --install git+https://github.com/shotgunsoftware/python-api.git
(cd packages/notgun && rez build -i)
(cd packages/notgun-launcher && rez build -i)
(cd packages/notgun-nuke && rez build -i)