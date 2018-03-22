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
This file acts as a login shell for the door user.
It updates the modified time on AUTH_FILE to be AUTH_TIMEOUT seconds in the future

doorvim.py uses AUTH_FILE to decide to unlock the door. It unlocks only if the file's
last-modified time is in the future. Additionally it deletes the file after unlocking
the door, to prevent people slipping in after you.
"""

from __future__ import print_function

import os
import time
import argparse

AUTH_FILE = "/home/door/doorvim/.auth"
MAX_TIMEOUT = 60*60*24*365.25

def main():
    parser = argparse.ArgumentParser(description="Authenticate doorvim")
    parser.add_argument('-c', metavar="MM:SS", dest='timeout',
                        help="Allow doorvim to open the door for the next TIMEOUT duration of time")
    args = parser.parse_args()
    if args.timeout is None:
        args.timeout = raw_input("Timeout? > ")
    try:
        if ":" in args.timeout:
            minutes, seconds = args.timeout.split(":")
            if minutes < 0 or seconds < 0:
                raise ValueError
            timeout = int(minutes) * 60 + int(seconds)
        else:
            timeout = int(args.timeout)
            if timeout < 0:
                raise ValueError
    except (ValueError, TypeError):
        print("Doorvim Error\n Invalid duration:", args.timeout)
    else:
        if timeout > MAX_TIMEOUT:
            print("Doorvim Error\nTimeout too large:", args.timeout)
            return
        elif timeout == 0:
            try:
                os.remove(AUTH_FILE)
            except OSError as e:
                if e.errno != 2:
                    print("Doorvim Deauthentication Failed!", e, sep='\n')
                    return
            print("Success\nDoorvim no longer authenticated")
        else:
            expiry = time.time() + timeout
            try:
                with open(AUTH_FILE, 'a'):
                    os.chmod(AUTH_FILE, 0o660)
                    os.utime(AUTH_FILE, (expiry, expiry))
            except (IOError, OSError) as e:
                print("Doorvim Authentication Failed!", e, sep='\n')
            else:
                print("Success\nDoorvim now authenticated for {}m {}s".format(*divmod(timeout, 60)))

if __name__ == '__main__':
    main()
