#!/usr/bin/env python

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
Interface for authenticating and storing short lists of users
with phone number passwords.
"""


import json
from collections import OrderedDict
import string
import hashlib
import os
from binascii import hexlify, unhexlify
import logging

__all__ = [
  "encode_as_digits",
  'ENCODE',
  'User',
  'load_users',
  'save_new_user',
  'authenticate_user',
  'VALID_PASS_CHARS'
]

# Valid passwords consist of [A-Za-z0-9]+ but are case insensitive
VALID_PASS_CHARS = string.digits + string.ascii_letters
ENCODE = {
  '0': b'0',
  '1': b'1',
  '2': b'2', 'A': b'2', 'B': b'2', 'C': b'2',
  '3': b'3', 'D': b'3', 'E': b'3', 'F': b'3',
  '4': b'4', 'G': b'4', 'H': b'4', 'I': b'4',
  '5': b'5', 'J': b'5', 'K': b'5', 'L': b'5',
  '6': b'6', 'M': b'6', 'N': b'6', 'O': b'6',
  '7': b'7', 'P': b'7', 'Q': b'7', 'R': b'7', 'S': b'7',
  '8': b'8', 'T': b'8', 'U': b'8', 'V': b'8',
  '9': b'9', 'W': b'9', 'X': b'9', 'Y': b'9', 'Z': b'9'
}
LOG = logging.getLogger(__name__)

# JSON parser
def disallow_floats(_):
  raise ValueError("Floating point numbers/constants not allowed in config")
def identity(obj):
  return obj
JSON_DECODE_KWARGS = {
  'object_hook': identity,  # object_pairs_hook takes priority
  'object_pairs_hook': OrderedDict,
  'strict': True,
  'parse_constant': disallow_floats,
  'parse_float': disallow_floats,
  'parse_int': identity
}
JSON_ENCODE_KWARGS = {
  'sort_keys': True,
  'indent': 2,
  'separators': (',', ': '),

}
CONFIG_READER = json.JSONDecoder(**JSON_DECODE_KWARGS)
CONFIG_WRITER = json.JSONEncoder(**JSON_ENCODE_KWARGS)

def encode_as_digits(plain):
  """Idempotent function that encodes a plaintext as phone digits
  raises ValueError if the text cannot be encoded"""
  try:
    return b''.join(ENCODE[string.upper(L)] for L in plain)
  except KeyError as ex:
    raise ValueError(ex.message)

class User(object):
  """Represents a known user of Doorman"""

  HASH_ALG = 'sha256'  # Can change this
  HASH_LEN = hashlib.new(HASH_ALG).digest_size

  SUPPORTED_OPTS = {'hash', 'salt', 'greeting', 'pass', 'enable', 'disable'}

  AUTH_SPEC_ERR = "Exactly one of {hash, pass} must be specified."
  PASS_LEN_ERR = "Password must be non-empty."
  PASS_CHARS_ERR = "Password must consist of only letters and numbers."
  HASH_LEN_ERR = "Hash must be exactly %d hex-encoded bytes" % HASH_LEN \
               + " (got %d)."
  UNSUP_OPT_ERR = "Unsupported options found: %s"

  def __init__(self, name, props):
    """Initializes a user with the given name and attributes"""
    self.name = name
    self.greeting = props.get('greeting', None)

    # salted password hash in hex
    hexdigest = string.strip(props.get('hash', b''))
    # password in plaintext
    self.passw = password = string.strip(props.get('pass', b''))

    self.salt = salt = unhexlify(props.get('salt', b'').strip())
    self._hash_obj = hashlib.new(self.HASH_ALG, salt)

    # At this point all the fields are filled in
    # so we may call instance methods without fear

    remaining = set(props) - self.SUPPORTED_OPTS
    if remaining:
      msg = self.UNSUP_OPT_ERR % ', '.join(sorted(remaining))
      raise self._invalid_spec(msg)

    # Ensure only one of pass or hash is specified
    if bool(password) == bool(hexdigest):
      raise self._invalid_spec(self.AUTH_SPEC_ERR)

    # Set self.digest to reflect the given plaintext password or hex digest
    # if password == '':
    #   raise self._invalid_spec(self.PASS_LEN_ERR)
    if password:
      try:
        digits = encode_as_digits(password.strip())
      except ValueError:
        raise self._invalid_spec(self.PASS_CHARS_ERR)
      hash_obj = self.hash_obj
      hash_obj.update(digits)
      self.digest = hash_obj.digest()
    else:  # hash was specified instead
      try:
        self.digest = unhexlify(hexdigest.strip())
        assert len(self.digest) == self.HASH_LEN
      except (ValueError, AssertionError):
        raise self._invalid_spec(self.HASH_LEN_ERR)

  @property
  def hash_obj(self):
    """A hash object initialized to the user's salt"""
    return self._hash_obj.copy()

  def check_pass(self, digits):
    """Returns whether the given telephone digits are the user's password"""
    hash_obj = self.hash_obj
    hash_obj.update(digits)
    match = True
    for i, j in zip(hash_obj.digest(), self.digest):
      match &= (i == j)
    return match

  def _invalid_spec(self, err):
    """Formats an exception for the constructor"""
    return ValueError("(In user %s): %s"%(self.name, err))

def authenticate_user(dtmf, users):
  """Matches the password to a user and returns the corresponding \
User object if found.
  Otherwise, returns None. Raises no exceptions under normal operation."""
  try:
    digits = encode_as_digits(dtmf)
  except ValueError:
    return None

  for user in users:
    if user.check_pass(digits):
      return user

  return None

def read_config(filename):
  """Parse a JSON file and return the empty """
  LOG.debug("Attempting to read config from " + filename)
  try:
    with open(filename, 'r') as f:
      return CONFIG_READER.decode(f.read())
  except OSError:
    LOG.error("Could not read " + filename)
  except ValueError:
    LOG.error(filename + "was not valid JSON (is it empty?)")
  return OrderedDict()

def load_users(filename='users.json'):
  """Loads users from the config file and returns the list"""
  config = read_config(filename)
  users = []

  for name, options in config.items():
    LOG.debug("Loading user %s from file " % name + filename)
    if not int(options.get("disable", False)) \
       and int(options.get("enable", True)):
      user = User(name, options)
      users.append(user)

  return users

def save_new_user(name, passw, usehash=True, saltlen=16,
                  filename='users.json'):
  """Adds a user to the config file"""
  config = read_config(filename)

  code = encode_as_digits(passw)
  salt = os.urandom(saltlen)

  options = {}
  options['salt'] = hexlify(salt)

  hash_obj = hashlib.new(User.HASH_ALG, salt)
  hash_obj.update(code)
  digest = hash_obj.hexdigest()
  if usehash:
    options['hash'] = digest
  else:
    options['pass'] = passw

  config[name] = options

  with open(filename, 'w') as f:
    for chunk in CONFIG_WRITER.iterencode(config):
      f.write(chunk)
