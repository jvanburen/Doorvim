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

from __future__ import division

import user
from iterface import Vgetty
from time import sleep

HELLO = None  # "sounds/prompt.m4a"  # Convert to modem format
UNAUTH = None  # "sounds/no.m4a"  # Convert to modem format
GOODBYE = None  # "sounds/goodbye.m4a"  # Convert to modem format

class Doorvim(Vgetty):
  def unlock(self):
    self.dial("#9")

def main():
  users = user.load_users()
  doorvim = Doorvim()
  code = doorvim.read_dtmf_string(prompt=HELLO)
  if code is None:
  	doorvim.play(GOODBYE)
  	return 0
  user = authenticate_user(code)
  if user is None:
  	doorvim.play(UNAUTH)
  	sleep(0.5)
  else:
  	doorvim.play(user.greeting)
  	doorvim.unlock()
  doorvim.play(GOODBYE)
  return 0

if __name__ == '__main__':
  exit(main())
