#
# Copyright (c) 2010-2016, Fabric Software Inc. All rights reserved.
#

import clang
from cpp_type_expr_parser import *

class Namespace:

  def __init__(self, parent_namespace, path):
    self.parent_namespace = parent_namespace
    self.path = path
    self.sub_namespaces = {}
    self.cpp_type_exprs = {}
    self.usings = []

  def maybe_get_child_namespace(self, child_namespace_path):
    namespace = self
    for i in range(0, len(child_namespace_path)):
      child_namespace_path_component = child_namespace_path[i]
      sub_namespace = namespace.sub_namespaces.get(child_namespace_path_component)
      if not sub_namespace:
        for using in self.usings:
          sub_namespace = using.sub_namespaces.get(child_namespace_path_component)
          if sub_namespace:
            break
      if not sub_namespace:
        return None
      namespace = sub_namespace
    return namespace

  def maybe_resolve_child_namespace(self, child_namespace_path):
    namespace = self
    while namespace:
      child_namespace = namespace.maybe_get_child_namespace(child_namespace_path)
      if child_namespace:
        return child_namespace
      namespace = namespace.parent_namespace
    return None

  def maybe_find_cpp_type_expr(self, child_namespace_path):
    namespace = self
    for i in range(0, len(child_namespace_path)):
      child_namespace_path_component = child_namespace_path[i]
      if i == len(child_namespace_path) - 1:
        cpp_type_expr = namespace.cpp_type_exprs.get(child_namespace_path_component)
        if not cpp_type_expr:
          for using in self.usings:
            cpp_type_expr = using.cpp_type_exprs.get(child_namespace_path_component)
            if cpp_type_expr:
              break
        if not cpp_type_expr:
          return None
      else:
        sub_namespace = namespace.sub_namespaces.get(child_namespace_path_component)
        if not sub_namespace:
          for using in self.usings:
            sub_namespace = using.sub_namespaces.get(child_namespace_path_component)
            if sub_namespace:
              break
        if not sub_namespace:
          return None
        namespace = sub_namespace
    return cpp_type_expr

class NamespaceMgr:

  def __init__(self):
    # [pzion 20160311] Each member in the namespace is either a Clang cursor that is the
    # definition of the type (or typedef/using; if there is no definition, it's the declaration),
    # or a dict in the case that it's a nested namespace
    self.root_namespace = Namespace(None, [])
    def maybe_lookup_cpp_type_expr(name):
      return self.root_namespace.maybe_find_cpp_type_expr(name.split("::"))
    self.cpp_type_expr_parser = Parser(maybe_lookup_cpp_type_expr)

  def _resolve_namespace(self, namespace_path):
    namespace = self.root_namespace.maybe_get_child_namespace(namespace_path)
    if not namespace:
      raise Exception("Failed to resolve namespace " + "::".join(namespace_path))
    return namespace

  def add_nested_namespace(self, namespace_path, nested_namespace_name):
    namespace = self._resolve_namespace(namespace_path)
    namespace_member = namespace.sub_namespaces.setdefault(nested_namespace_name, Namespace(namespace, namespace_path + [nested_namespace_name]))
    return namespace_path + [nested_namespace_name]

  def add_type(self, namespace_path, type_name, cpp_type_expr):
    namespace = self._resolve_namespace(namespace_path)
    namespace.cpp_type_exprs.setdefault(type_name, cpp_type_expr)
    return Named("::".join(namespace_path + [type_name]))

  def add_using_namespace(self, namespace_path, import_namespace_path):
    namespace = self._resolve_namespace(namespace_path)
    import_namespace = namespace.maybe_resolve_child_namespace(import_namespace_path)
    if not import_namespace:
      raise Exception("Failed to resolve namespace '%s' inside namespace '%s'" % ("::".join(import_namespace_path), "::".join(namespace_path)))
    namespace.usings.append(import_namespace)

  def globalize_simple_cpp_type_name(self, current_namespace_path, type_name):
    nested_type_name = type_name.split("::")
    current_namespace = self._resolve_namespace(current_namespace_path)
    while current_namespace:        
      cpp_type_expr = current_namespace.maybe_find_cpp_type_expr(nested_type_name)
      if cpp_type_expr:
        nested_type_name = current_namespace.path + nested_type_name
        break
      current_namespace = current_namespace.parent_namespace
    return "::".join(nested_type_name)

  def globalize_cpp_type_expr(self, current_namespace_path, cpp_type_expr):
    def globalize_name(name):
      return self.globalize_simple_cpp_type_name(current_namespace_path, name)
    cpp_type_expr.tranform_names(globalize_name)

  def resolve_cpp_type_expr(self, current_namespace_path, value):
    current_namespace = self._resolve_namespace(current_namespace_path)
    if isinstance(value, clang.cindex.Type):
      type_name = value.spelling
    elif isinstance(value, basestring):
      type_name = value
    else:
      raise Exception("unexpected value type")
    cpp_type_expr = self.cpp_type_expr_parser.parse(type_name)
    self.globalize_cpp_type_expr(current_namespace_path, cpp_type_expr)
    return cpp_type_expr

