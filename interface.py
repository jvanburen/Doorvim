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
import sys, os
from signal import SIGPIPE, alarm, signal, SIGALRM

"""
Interface to the vgetty voice library for Doorvim
"""

__all__ = [
  "DTMF_WAIT",
  "AUTOSTOP",
  "Vgetty"
]

# Source: https://en.wikipedia.org/wiki/DTMF
# LO_TONES = [697, 770, 852, 941]
# HI_TONES = [1209, 1336, 1477, 1633]
# DTONES = [(lo, hi) for lo in LO_TONES for hi in HI_TONES]
# DTMF_TONE = dict(zip("123A456B789C*0#D", DTONES))

DTMF_WAIT = 30
AUTOSTOP = True

class Vgetty(object):
  """Static singleton representing the voice library"""
  __instance = None

  def __new__(cls):
    if Vgetty.__instance is None:
      Vgetty.__instance = object.__new__(cls)
    return Vgetty.__instance

  def __init__(self):
    if Vgetty.__instance is not None: return
    def vin_timeout(signum, frame):
      raise IOError("Timeout while waiting for vgetty response")
    signal(SIGALRM, vin_timeout)
    
    vin_fd = int(os.environ["VOICE_INPUT"])
    vout_fd = int(os.environ["VOICE_OUTPUT"])
    self._voice_pid = int(os.environ["VOICE_PID"])
    self._vin = os.fdopen(vin_fd, "r", 1)
    self._vout = os.fdopen(vout_fd, "w", 0)

    # The state is the last thing the library said to us
    # or None if disabled / unknown state
    self.status = "INIT"  # Special state

    # initial setup with library 
    recv = self.waitfor("HELLO SHELL")
    self.send("HELLO VOICE PROGRAM")
    self.waitfor()

    if AUTOSTOP:
      self.send("AUTOSTOP ON")
      self.waitfor()

  def __del__(self):
    if self.enabled:
      self.send("GOODBYE")
      self.waitfor("GOODBYE SHELL")
    self._vin.close()
    self._vout.close()
    self.status = None

  @property
  def enabled(self):
      return self.status is not None

  def send(self, msg):
    """Send a message to the voice library"""
    assert self.enabled, "Voice library has been disabled"
    self._vout.write(msg+'\n')
    os.kill(self._voice_pid, SIGPIPE)

  def _blocking_recv(self):
    assert self.enabled, "Voice library has been disabled"
    return self._vin.readline()

  def _recv(self, timeout):
    assert self.enabled, "Voice library has been disabled"
    alarm(timeout)  # Plenty of time by default
    data = self._blocking_recv()
    alarm(0)  # Disable alarm
    return data

  def recv(self, *expected, **timeout):
    """Recieve a message from the voice library.
    If expecting certain responses, error if unexpected responses.
    timeout is in seconds (or False)"""
    data = self._recv(timeout.get('timeout', 10))
    recv = data.decode('ascii').strip()
    self.status = recv

    if recv == "ERROR":
      self.status = None  # unknown state
      raise IOError("Voice library reported an error")

    if expected and recv not in expected:
      fmt = (', '.join(expected), recv)
      self.status = None  # unknown state
      raise ValueError("Expected one of {%s}, got '%s'"%fmt)
    return recv

  def waitfor(self, response='READY', timeout=10):
    """Waits with long timeout for response from the voice server
    timeout is in seconds (or False)
    Throws error if invalid response"""
    self.recv(response, timeout=timeout)

  def ignoreuntil(self, resp, *resps, **timeout):
    """Throws away responses until receiving one of the given responses,
    then returns it"""
    resps.append(resp)
    alarm(timeout.get('timeout', 10))
    recv = self._blocking_recv().decode('ascii').strip()
    while recv not in resps:
      recv = self._blocking_recv().decode('ascii').strip()
    alarm(0)
    self.status = recv
    return recv

  def play(self, filename):
    """Play an audio file"""
    if not filename:
      return
    self.send("PLAY %s" % filename)
    self.recv('PLAYING')
    self.waitfor()

  def beep(self, freq=None, len=None):
    """Play a beep (len in ms)"""
    self.send("BEEP %d %d" % (freq or '', '' if not freq else (len or '')))
    self.waitfor("BEEPING")
    timeout = 11 + (bool(len) and len // 1000)
    self.waitfor(timeout=timeout)

  def dial(self, number):
    """Dial a number"""
    self.send("DIAL %s"%number)
    self.waitfor("DIALING")
    self.waitfor()

  def read_dtmf_string(self, waittime=30, prompt=None):
    """Read a dtmf code string. '*' clear the string and # ends it.
    time is in seconds
    Returns the string read, or None if silence was detected
    prompt is None or a filename"""

    self.send("AUTOSTOP ON")
    self.waitfor()

    self.send("ENABLE EVENTS")
    self.waitfor()

    if prompt:
      self.send("PLAY %s" % filename)
      self.ignoreuntil("PLAYING", "READY")

    self.send("WAIT %d" % waittime)  # Enables events
    self.waitfor("WAITING")

    recvd = []
    while self.status and self.status != 'READY':
      self.recv(timeout=waittime)
      if self.status == "RECEIVED_DTMF":
        code = self.recv()
        if code == '*':
          recvd = []  # clear
        elif code == '#':
          self.send("STOP")
          self.waitfor()
        elif code in "0123456789":
          recvd.append(code)
        else:
          pass # ignore the other codes

      elif self.status == "SILENCE_DETECTED":
        self.send("STOP")
        self.waitfor()
        recvd = None

    self.send("DISABLE EVENTS")
    self.waitfor()

    if not AUTOSTOP:
      self.send("AUTOSTOP OFF")
      self.waitfor()

    return None if recvd is None else ''.join(recvd)

