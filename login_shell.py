#!/usr/bin/python

# The MIT License (MIT)
# Copyright (c) 2018 Jacob Van Buren

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
This file allows you to authenticate the file for 
"""

from __future__ import print_function

import os
import time

AUTH_FILE = "/home/door/doorvim/.auth"
AUTH_TIMEOUT = 120 # seconds

def main():
    action = raw_input("Action (auth/revoke)> ")
    if action == "auth":
        try:
            expiry = time.time() + AUTH_TIMEOUT
            with open(AUTH_FILE, 'a'):
                os.chmod(AUTH_FILE, 0o660)
                os.utime(AUTH_FILE, (expiry, expiry))
        except (IOError, OSError):
            print("fail")
            exit(1)
    elif action == "revoke":
        try:
            os.remove(AUTH_FILE)
        except OSError as e:
            if e.errno != 2:
                print('fail')
                exit(1)
    else:
        print("unrecognized")
        exit(1)
    exit(0)

if __name__ == '__main__':
    main()
