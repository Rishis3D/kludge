{######################################################################}
{# Copyright (c) 2010-2016, Fabric Software Inc. All rights reserved. #}
{######################################################################}
//////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////
//
// C++ definitions for {{ext.name}} extension
// Automatically generated by KLUDGE
// *** DO NOT EDIT ***
//
//////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////
// Inclusion of FabricEDK and EDK initialization
//////////////////////////////////////////////////////////////////////////////

#include <FabricEDK.h>

#define FABRIC_EDK_EXT_{{ext.name}}_DEPENDENT_EXTS \
  { \
    { 0, 0, 0, 0, 0 } \
  }
IMPLEMENT_FABRIC_EDK_ENTRIES({{ext.name}})

//////////////////////////////////////////////////////////////////////////////
// Includes of C++ global headers for extension
//////////////////////////////////////////////////////////////////////////////

// To include C++ global headers in your extension, add to
// gen_script.kludge.kl:
//
// ext.add_cpp_global_include('string')  # -> #include <string>
//
// You can also include headers on a per-declaration basis.
//
{% for cpp_global_include in ext.cpp_global_includes %}
#include <{{cpp_global_include}}>
{% endfor %}

//////////////////////////////////////////////////////////////////////////////
// Global Functions
//////////////////////////////////////////////////////////////////////////////

{% for func in ext.funcs %}
{{ func.render('cpp') }}
{% endfor %}