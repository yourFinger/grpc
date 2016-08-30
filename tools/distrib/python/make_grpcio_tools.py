#!/usr/bin/env python

# Copyright 2016, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function

import errno
import filecmp
import glob
import os
import os.path
import shutil
import subprocess
import sys
import traceback
import uuid

DEPS_FILE_CONTENT="""
# Copyright 2016, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# AUTO-GENERATED BY make_grpcio_tools.py!
CC_FILES={cc_files}
PROTO_FILES={proto_files}

CC_INCLUDE={cc_include}
PROTO_INCLUDE={proto_include}
"""

# Bazel query result prefix for expected source files in protobuf.
PROTOBUF_CC_PREFIX = '//:src/'
PROTOBUF_PROTO_PREFIX = '//:src/'

GRPC_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '..', '..', '..'))

GRPC_PYTHON_ROOT = os.path.join(GRPC_ROOT, 'tools', 'distrib',
                                'python', 'grpcio_tools')

GRPC_PYTHON_PROTOBUF_RELATIVE_ROOT = os.path.join('third_party', 'protobuf', 'src')
GRPC_PROTOBUF = os.path.join(GRPC_ROOT, GRPC_PYTHON_PROTOBUF_RELATIVE_ROOT)
GRPC_PROTOC_PLUGINS = os.path.join(GRPC_ROOT, 'src', 'compiler')
GRPC_PYTHON_PROTOBUF = os.path.join(GRPC_PYTHON_ROOT, 'third_party', 'protobuf',
                                    'src')
GRPC_PYTHON_PROTOC_PLUGINS = os.path.join(GRPC_PYTHON_ROOT, 'grpc_root', 'src',
                                          'compiler')
GRPC_PYTHON_PROTOC_LIB_DEPS = os.path.join(GRPC_PYTHON_ROOT,
                                           'protoc_lib_deps.py')

GRPC_INCLUDE = os.path.join(GRPC_ROOT, 'include')
GRPC_PYTHON_INCLUDE = os.path.join(GRPC_PYTHON_ROOT, 'grpc_root', 'include')

BAZEL_DEPS = os.path.join(GRPC_ROOT, 'tools', 'distrib', 'python', 'bazel_deps.sh')
BAZEL_DEPS_PROTOC_LIB_QUERY = '//:protoc_lib'
BAZEL_DEPS_COMMON_PROTOS_QUERY = '//:well_known_protos'


def bazel_query(query):
  output = subprocess.check_output([BAZEL_DEPS, query])
  return output.splitlines()

def get_deps():
  """Write the result of the bazel query `query` against protobuf to
     `out_file`."""
  cc_files_output = bazel_query(BAZEL_DEPS_PROTOC_LIB_QUERY)
  cc_files = [
      name[len(PROTOBUF_CC_PREFIX):] for name in cc_files_output
      if name.endswith('.cc') and name.startswith(PROTOBUF_CC_PREFIX)]
  proto_files_output = bazel_query(BAZEL_DEPS_COMMON_PROTOS_QUERY)
  proto_files = [
      name[len(PROTOBUF_PROTO_PREFIX):] for name in proto_files_output
      if name.endswith('.proto') and name.startswith(PROTOBUF_PROTO_PREFIX)]
  deps_file_content = DEPS_FILE_CONTENT.format(
      cc_files=cc_files,
      proto_files=proto_files,
      cc_include=repr(GRPC_PYTHON_PROTOBUF_RELATIVE_ROOT),
      proto_include=repr(GRPC_PYTHON_PROTOBUF_RELATIVE_ROOT))
  return deps_file_content

def long_path(path):
  if os.name == 'nt':
    return '\\\\?\\' + path
  else:
    return path

def main():
  os.chdir(GRPC_ROOT)

  for source, target in [
      (GRPC_PROTOBUF, GRPC_PYTHON_PROTOBUF),
      (GRPC_PROTOC_PLUGINS, GRPC_PYTHON_PROTOC_PLUGINS),
      (GRPC_INCLUDE, GRPC_PYTHON_INCLUDE)]:
    for source_dir, _, files in os.walk(source):
      target_dir = os.path.abspath(os.path.join(target, os.path.relpath(source_dir, source)))
      try:
        os.makedirs(target_dir)
      except OSError as error:
        if error.errno != errno.EEXIST:
          raise
      for relative_file in files:
        source_file = os.path.abspath(os.path.join(source_dir, relative_file))
        target_file = os.path.abspath(os.path.join(target_dir, relative_file))
        shutil.copyfile(source_file, target_file)

  try:
    protoc_lib_deps_content = get_deps()
  except Exception as error:
    # We allow this script to succeed even if we couldn't get the dependencies,
    # as then we can assume that even without a successful bazel run the
    # dependencies currently in source control are 'good enough'.
    sys.stderr.write("Got non-fatal error:\n")
    traceback.print_exc(file=sys.stderr)
    return
  # If we successfully got the dependencies, truncate and rewrite the deps file.
  with open(GRPC_PYTHON_PROTOC_LIB_DEPS, 'w') as deps_file:
    deps_file.write(protoc_lib_deps_content)

if __name__ == '__main__':
  main()

