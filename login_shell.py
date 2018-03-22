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
LOG_FILE = "/home/door/doorvim/visitors.log"
MAX_TIMEOUT = 60*60*24 # seconds (1 day)
LOG = None

def main():
  def success(message):
    msg = "Success\n" + message
    print(msg)
    LOG.info(msg)
    exit(0)
  def fail(message):
    msg = "Doorvim Error\n" + message
    print(msg)
    LOG.warn(msg)
    exit(0)
  def nonnegint(s):
    i = int(s)
    if i < 0:
      raise ValueError("Negative integers not allowed here")
    return i

  parser = argparse.ArgumentParser(description="Authenticate doorvim")
  parser.add_argument('-c', metavar="MM:SS", dest='timeout',
                      help="Allow doorvim to open the door for the next TIMEOUT duration of time")
  args = parser.parse_args()
  if args.timeout is None:
    args.timeout = raw_input("Timeout? > ")
  LOG.info("Got Login request for " + args.timeout)
  try:
    if ":" in args.timeout:
      minutes, seconds = args.timeout.split(":")
      timeout = nonnegint(minutes) * 60 + nonnegint(seconds)
    else:
      timeout = nonnegint(args.timeout)
  except (ValueError, TypeError):
    fail("Invalid duration:", args.timeout)
  else:
    if timeout > MAX_TIMEOUT:
      fail("Timeout too large:", args.timeout)
    elif timeout == 0:
      try:
        os.remove(AUTH_FILE)
      except OSError as e:
        if e.errno != 2:
          fail("Deauthentication Failed!\n" + str(e))
      success("Doorvim no longer authenticated")
    else:
      expiry = time.time() + timeout
      try:
        with open(AUTH_FILE, 'a'):
          os.chmod(AUTH_FILE, 0o660) # chmod first!
          os.utime(AUTH_FILE, (expiry, expiry))
      except (IOError, OSError) as e:
        fail("Doorvim Authentication Failed!", e, sep='\n')
      else:
        hours, timeout = divmod(timeout, 3600)
        minutes, seconds = divmod(timeout, 60)
        if hours > 0:
          success("Doorvim now authenticated for\n{}h {}m {}s".format(hours, minutes, seconds))
        elif minutes > 0:
          success("Doorvim now authenticated for\n{}m {}s".format(minutes, seconds))
        else:
          success("Doorvim now authenticated for\n{}s".format(seconds))

if __name__ == '__main__':
  logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)
  logging.info("Starting {} as {}".format(__file__, __name__))
  LOG = logging.getLogger(__name__)
  try:
    main()
  except Exception as e:
    LOG.error(e)
    raise
  finally:
    logging.shutdown()
