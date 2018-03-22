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
It has two commands, authenticate and revoke (case insensitive).
authenticate updates the modified time on AUTH_FILE to be AUTH_TIMEOUT seconds in the future
revoke deletes AUTH_FILE

doorvim.py uses AUTH_FILE to decide to unlock the door. It unlocks only if the file's
last-modified time is in the future. Additionally it deletes the file after unlocking
the door, to prevent people slipping in after you.
"""

from __future__ import print_function

import os
import time
import argparse

AUTH_FILE = "/home/door/doorvim/.auth"
AUTH_TIMEOUT = 120 # seconds

def main():
    parser = argparse.ArgumentParser(description="Authenticate doorvim")
    parser.add_argument('-c', metavar="ACTION", dest='action',
                        help="What to do, either\
                        'authenticate' (Authenticates doorvim for the next {} seconds)\
                        or 'revoke' (Revokes any existing authentication)"
                        .format(AUTH_TIMEOUT))
    args = parser.parse_args()
    if args.action is None:
        args.action = raw_input("Action (auth/revoke)> ")
    if args.action.lower() == "authenticate":
        try:
            expiry = time.time() + AUTH_TIMEOUT
            with open(AUTH_FILE, 'a'):
                os.chmod(AUTH_FILE, 0o660)
                os.utime(AUTH_FILE, (expiry, expiry))
        except (IOError, OSError) as e:
            print("Doorvim Error\nAuthentication Failed!:", e, sep='\n')
            exit(1)
        print("Success\nDoorvim authenticated for {} seconds".format(AUTH_TIMEOUT))
    elif args.action.lower() == "revoke":
        try:
            os.remove(AUTH_FILE)
        except OSError as e:
            if e.errno != 2:
                print("Doorvim Error\nDeauthentication Failed!:", e, sep='\n')
                exit(1)
        print("Success\nDoorvim no longer authenticated")
    else:
        print("Doorvim Error\nUnrecognized action:", args.action)
        exit(1)
    exit(0)

if __name__ == '__main__':
    main()
