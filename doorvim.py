#!/usr/bin/vm shell -S /usr/bin/python

# The MIT License (MIT)
# Copyright (c) 2015 Jacob Van Buren

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
Doorvim

A vgetty door-answering machine for my apartment.
Set this program as call_program in /etc/mgetty/voice.conf
"""

from __future__ import division
from interface import Vgetty
import time
import logging
import os

HELLO = "/home/door/sounds/prompt.pcm"  # Convert to modem format
UNAUTH = "/home/door/sounds/no.pcm"  # Convert to modem format
GOODBYE = "/home/door/sounds/goodbye.pcm"  # Convert to modem format
AUTH_FILE = "/home/door/.auth"
LOG_FILE = '/home/door/visitors.log'  # '/users/jacob/Desktop/visitors.log'

class Doorvim(Vgetty):
  def unlock(self):
    self.dial("#9")

def is_authenticated():
  try:
    st = os.stat(AUTH_FILE)
  except OSError:
    return False
  else:
    try:
      os.remove(AUTH_FILE)
    except OSError, IOError:
      pass
    expiry_time = st.st_mtime
    return time.time() < expiry_time

def main():
  """Program entry point"""
  with Doorvim() as doorvim:
    code = doorvim.read_dtmf_string(prompt=HELLO)
    if code is None:
      doorvim.play(GOODBYE)
      return 0
    if is_authenticated():
      LOG.info("authenticated ")
      doorvim.play(HELLO)
      doorvim.unlock()
    else:
      LOG.info("not authenticated ")
      doorvim.play(UNAUTH)
      sleep(0.5)
      doorvim.play(GOODBYE)
  return 0

if __name__ == '__main__':
  logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)

  logging.info("Starting " + __name__)
  LOG = logging.getLogger(__name__)
  try:
    RETC = main()
  finally:
    logging.shutdown()
  exit(RETC)



