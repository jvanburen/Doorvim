# Doorvim

A vgetty door-answering machine for my apartment.

### Installation

- Ensure vgetty is installed and functioning
- Create a user named `door`
- Clone this repo to `/home/door/doorvim/`
- Set `/home/door/doorvim/doorvim.py` as `call_program` in /etc/mgetty/voice.conf
- Set the login shell for `door` to be `/home/door/doorvim/login_shell.py`
- Change the password for the user `door` to be the password to unlock the door.

### Companion App
There is a Workflow for automating this easily from an iPhone, available at https://workflow.is/workflows/277a80cd1cb1433882db6220137e3699

