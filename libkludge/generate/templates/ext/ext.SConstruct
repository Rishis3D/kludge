{######################################################################}
{# Copyright (c) 2010-2016, Fabric Software Inc. All rights reserved. #}
{######################################################################}
##############################################################################
##############################################################################
##
## Automatically generated by KLUDGE
## *** DO NOT EDIT ***
##
##############################################################################
##############################################################################

import os, sys

extname = '{{ ext.name }}'
basename = '{{ ext.name }}'

try:
  fabricPath = os.environ['FABRIC_DIR']
except:
  print "You must set FABRIC_DIR in your environment."
  print "Refer to README.txt for more information."
  sys.exit(1)
SConscript(os.path.join(fabricPath, 'Samples', 'EDK', 'SConscript'))
Import('fabricBuildEnv')

if os.environ.get('CC'):
  fabricBuildEnv['CC'] = os.environ.get('CC')
if os.environ.get('CXX'):
  fabricBuildEnv['CXX'] = os.environ.get('CXX')
{% for cpp_flag in ext.cpp_flags %}
fabricBuildEnv.Append(CPPFLAGS = ['{{ cpp_flag }}'])
{% endfor %}
{% for cpp_define in ext.cpp_defines %}
fabricBuildEnv.Append(CPPDEFINES = ['{{ cpp_define }}'])
{% endfor %}
if os.environ.get('CPPPATH'):
  fabricBuildEnv.Append(CPPPATH = [os.environ.get('CPPPATH')])
{% for cpp_include_dir in ext.cpp_include_dirs %}
fabricBuildEnv.Append(CPPPATH = ['{{ cpp_include_dir }}'])
{% endfor %}
{% for lib_dir in ext.lib_dirs %}
fabricBuildEnv.Append(LIBPATH = ['{{ lib_dir }}'])
{% endfor %}
{% for lib in ext.libs %}
fabricBuildEnv.Append(LIBS = ['{{ lib }}'])
{% endfor %}

fabricBuildEnv.SharedLibrary(
  '-'.join([extname, fabricBuildEnv['FABRIC_BUILD_OS'], fabricBuildEnv['FABRIC_BUILD_ARCH']]),
  [basename + '.cpp']
  )
