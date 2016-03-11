#
# Copyright (c) 2010-2016, Fabric Software Inc. All rights reserved.
#

import clang

class Namespace:

  def __init__(self, parent_namespace, path):
    self.parent_namespace = parent_namespace
    self.path = path
    self.members = {}

  def maybe_find_clang_type_decl(self, child_namespace_member_path):
    first_namespace_member = self.members.get(child_namespace_member_path[0])
    if not first_namespace_member:
      return None
    elif len(child_namespace_member_path) > 1:
      if not isinstance(first_namespace_member, Namespace):
        return None
      return first_namespace_member.maybe_find_clang_type_decl(child_namespace_member_path[1:])
    else:
      if isinstance(first_namespace_member, Namespace):
        return None
      return first_namespace_member

class NamespaceMgr:

  base_types = [
    "char",
    "signed char",
    "unsigned char",
    "int",
    "signed int",
    "unsigned int",
    "short",
    "signed short",
    "unsigned short",
    "long",
    "signed long",
    "unsigned long",
    "long long",
    "signed long long",
    "unsigned long long",
    "signed",
    "unsigned",
    "float",
    "double",
    "size_t",
    "int8_t",
    "uint8_t",
    "int16_t",
    "uint16_t",
    "int32_t",
    "uint32_t",
    "int64_t",
    "uint64_t",
    ]

  def __init__(self):
    # [pzion 20160311] Each member in the namespace is either a Clang cursor that is the
    # definition of the type (or typedef/using; if there is no definition, it's the declaration),
    # or a dict in the case that it's a nested namespace
    self.root_namespace = Namespace(None, [])

  def _resolve_namespace(self, namespace_path):
    namespace = self.root_namespace
    for i in range(0, len(namespace_path)):
      namespace_value = namespace.members.get(namespace_path[i])
      if isinstance(namespace_value, Namespace):
        namespace = namespace_value
      else:
        raise Exception(
          "Namespace member '%s' is not a nested namespace" % "::".join(namespace_path[0:i+1])
          )
    return namespace

  def add_nested_namespace(self, namespace_path, nested_namespace_name):
    namespace = self._resolve_namespace(namespace_path)
    namespace_member = namespace.members.setdefault(nested_namespace_name, Namespace(namespace, namespace_path + [nested_namespace_name]))
    if not isinstance(namespace_member, Namespace):
      raise Exception(
        "Existing namespace member '%s' is not a nested namespace" % "::".join(namespace_path[0:i+1])
        )
    return namespace_path + [nested_namespace_name]

  def add_type_decl(self, namespace_path, clang_type_decl_cursor):
    namespace = self._resolve_namespace(namespace_path)
    type_name = clang_type_decl_cursor.spelling
    existing_namespace_member = namespace.members.get(type_name)
    if existing_namespace_member:
      pass # do something here to upgrade declarations to definitions
    namespace.members.setdefault(type_name, clang_type_decl_cursor)
    return namespace_path + [type_name]

  def get_nested_type_name(self, current_namespace_path, value):
    current_namespace = self._resolve_namespace(current_namespace_path)
    if isinstance(value, clang.cindex.Type):
      type_name = value.spelling
    elif isinstance(value, basestring):
      type_name = value
    else:
      raise Exception("unexpected value type")
    if type_name in self.base_types:
      return [type_name]
    nested_type_name = type_name.split("::")
    while current_namespace:        
      clang_type_decl = current_namespace.maybe_find_clang_type_decl(nested_type_name)
      if clang_type_decl:
        return current_namespace.path + nested_type_name
      current_namespace = current_namespace.parent_namespace
    return nested_type_name
