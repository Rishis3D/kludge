#
# Copyright (c) 2010-2016, Fabric Software Inc. All rights reserved.
#

import os, jinja2
from libkludge.cpp_type_expr_parser import Named, Simple, Template
from record import Record
from alias import Alias
from enum import Enum
from func import Func
from libkludge.types import InPlaceSelector
from libkludge.types import KLExtTypeAliasSelector
from libkludge.types import DirectSelector
from libkludge.types import WrappedSelector
from libkludge.types import EnumSelector

class Namespace:

  def __init__(
    self,
    ext,
    parent_namespace,
    cpp_name,
    kl_name,
    ):
    self.ext = ext
    self.parent_namespace = parent_namespace
    self.cpp_name = cpp_name
    if parent_namespace:
      self.nested_cpp_names = parent_namespace.nested_cpp_names + [cpp_name]
      self.nested_kl_names = parent_namespace.nested_cpp_names + [kl_name]
    else:
      self.nested_cpp_names = []
      self.nested_kl_names = []

    for method_name in [
      'error',
      'warning',
      'info',
      'debug',
      ]:
      setattr(self, method_name, getattr(ext, method_name))

  def create_child(self, cpp_name, kl_name):
    self.namespace_mgr.add_nested_namespace(self.nested_cpp_names, cpp_name)
    return Namespace(self.ext, self, cpp_name, kl_name)
  
  def resolve_cpp_type_expr(self, cpp_type_name):
    return self.namespace_mgr.resolve_cpp_type_expr(self.nested_cpp_names, cpp_type_name)

  @property
  def cpp_type_expr_parser(self):
    return self.ext.cpp_type_expr_parser

  @property
  def type_mgr(self):
    return self.ext.type_mgr

  @property
  def namespace_mgr(self):
    return self.ext.namespace_mgr

  @property
  def jinjenv(self):
    return self.ext.jinjenv

  @property
  def cpp_type_expr_to_record(self):
    return self.ext.cpp_type_expr_to_record

  def maybe_generate_kl_local_name(self, kl_local_name, cpp_type_expr):
    if not kl_local_name:
      assert isinstance(cpp_type_expr, Named)
      if isinstance(cpp_type_expr.components[-1], Simple):
        kl_local_name = cpp_type_expr.components[-1].name
      elif isinstance(cpp_type_expr.components[-1], Template) \
        and len(cpp_type_expr.components[-1].params) == 1 \
        and isinstance(cpp_type_expr.components[-1].params[0], Named) \
        and isinstance(cpp_type_expr.components[-1].params[0].components[0], Simple):
        kl_local_name = cpp_type_expr.components[-1].params[0].components[0].name
      else:
        raise Exception(str(cpp_type_expr) + ": unable to generate kl_local_name")
    return kl_local_name

  def add_namespace(self, cpp_name, kl_name=None):
    if not kl_name:
      kl_name = cpp_name
    return self.create_child(cpp_name, kl_name)

  def add_func(self, name, returns=None, params=[]):
    func = Func(self, name)
    if returns:
      func.returns(returns)
    for param in params:
      func.add_param(param)
    self.ext.decls.append(func)
    return func

  def add_alias(self, new_cpp_type_name, old_cpp_type_name):
    new_cpp_type_expr = Named([Simple(new_cpp_type_name)])
    old_cpp_type_expr = self.namespace_mgr.resolve_cpp_type_expr([], old_cpp_type_name)
    self.type_mgr.add_alias(new_cpp_type_expr, old_cpp_type_expr)
    new_kl_type_name = new_cpp_type_name
    old_dqti = self.type_mgr.get_dqti(old_cpp_type_expr)
    alias = Alias(self, new_kl_type_name, old_dqti.type_info)
    self.ext.decls.append(alias)
    return alias

  def add_in_place_type(
    self,
    cpp_type_name,
    kl_type_name = None,
    ):
    cpp_local_name = cpp_type_name
    cpp_global_name = '::'.join(self.nested_cpp_names + [cpp_local_name])
    cpp_type_expr = self.cpp_type_expr_parser.parse(cpp_global_name)
    kl_local_name = self.maybe_generate_kl_local_name(kl_type_name, cpp_type_expr)
    kl_global_name = '_'.join(self.nested_kl_names + [kl_local_name])
    self.type_mgr.add_selector(
      InPlaceSelector(
        self.jinjenv,
        kl_global_name,
        self.nested_cpp_names + [cpp_local_name],
        cpp_type_expr,
        )
      )
    record = Record(
      self,
      "InPlaceType: %s -> %s" % (kl_global_name, str(cpp_type_expr)),
      cpp_local_name,
      kl_local_name,
      self.type_mgr.get_dqti(cpp_type_expr).type_info,
      )
    self.ext.decls.append(record)
    self.namespace_mgr.add_type(
      self.nested_cpp_names,
      Named([cpp_type_expr.components[-1]]),
      cpp_type_expr,
      )
    self.cpp_type_expr_to_record[cpp_type_expr] = record
    return record

  def add_direct_type(
    self,
    cpp_type_name,
    kl_type_name = None,
    extends = None,
    forbid_copy = False,
    ):
    cpp_local_name = cpp_type_name
    cpp_global_name = '::'.join(self.nested_cpp_names + [cpp_local_name])
    cpp_type_expr = self.cpp_type_expr_parser.parse(cpp_global_name)
    kl_local_name = self.maybe_generate_kl_local_name(kl_type_name, cpp_type_expr)
    kl_global_name = '_'.join(self.nested_kl_names + [kl_local_name])
    if extends:
      extends_cpp_type_expr = self.cpp_type_expr_parser.parse(extends)
      extends = self.cpp_type_expr_to_record[extends_cpp_type_expr]
    self.type_mgr.add_selector(
      DirectSelector(
        self.jinjenv,
        kl_global_name,
        self.nested_cpp_names + [cpp_local_name],
        cpp_type_expr,
        False, #is_abstract,
        False, #no_copy_constructor,
        )
      )
    record = Record(
      self,
      "DirectType: %s -> %s [extends=%s forbid_copy=%s]" % (
        kl_global_name,
        str(cpp_type_expr),
        extends,
        forbid_copy,
        ),
      cpp_local_name,
      kl_local_name,
      self.type_mgr.get_dqti(cpp_type_expr).type_info,
      extends = extends,
      forbid_copy = forbid_copy,
      )
    self.ext.decls.append(record)
    self.namespace_mgr.add_type(
      self.nested_cpp_names,
      Named([cpp_type_expr.components[-1]]),
      cpp_type_expr,
      )
    self.cpp_type_expr_to_record[cpp_type_expr] = record
    return record

  def add_wrapped_type(
    self,
    cpp_type_name,
    kl_type_name = None,
    extends = None
    ):
    cpp_local_name = cpp_type_name
    cpp_global_name = '::'.join(self.nested_cpp_names + [cpp_local_name])
    cpp_type_expr = self.cpp_type_expr_parser.parse(cpp_local_name)
    assert isinstance(cpp_type_expr, Named) \
      and len(cpp_type_expr.components) >= 1 \
      and isinstance(cpp_type_expr.components[-1], Template) \
      and len(cpp_type_expr.components[-1].params) == 1 \
      and isinstance(cpp_type_expr.components[-1].params[0], Named) \
      and len(cpp_type_expr.components[-1].params[0].components) == 1 \
      and isinstance(cpp_type_expr.components[-1].params[0].components[0], Simple)
    kl_local_name = self.maybe_generate_kl_local_name(kl_type_name, cpp_type_expr)
    kl_global_name = '_'.join(self.nested_kl_names + [kl_local_name])
    if extends:
      extends_cpp_type_expr = self.cpp_type_expr_parser.parse(extends)
      extends = self.cpp_type_expr_to_record[extends_cpp_type_expr]
    self.type_mgr.add_selector(
      WrappedSelector(
        self.jinjenv,
        kl_global_name,
        self.nested_cpp_names + [cpp_local_name],
        cpp_type_expr,
        False, #is_abstract,
        False, #no_copy_constructor,
        )
      )
    record = Record(
      self,
      "WrappedType: %s -> %s" % (kl_global_name, str(cpp_type_expr)),
      cpp_local_name,
      kl_local_name,
      self.type_mgr.get_dqti(cpp_type_expr).type_info,
      extends = extends
      )
    self.ext.decls.append(record)
    self.namespace_mgr.add_type(
      self.nested_cpp_names,
      Named([cpp_type_expr.components[-1]]),
      cpp_type_expr,
      )
    self.cpp_type_expr_to_record[cpp_type_expr] = record
    return record

  def add_kl_ext_type_alias(
    self,
    cpp_local_name,
    kl_ext_name,
    kl_global_name,
    ):
    assert isinstance(cpp_local_name, basestring)
    cpp_type_expr = self.cpp_type_expr_parser.parse(cpp_local_name)
    assert isinstance(cpp_type_expr, Named)
    assert isinstance(kl_ext_name, basestring)
    self.ext.add_kl_require(kl_ext_name)
    assert isinstance(kl_global_name, basestring)
    self.type_mgr.add_selector(
      KLExtTypeAliasSelector(
        self.jinjenv,
        self.nested_cpp_names + [cpp_local_name],
        cpp_type_expr,
        kl_global_name,
        )
      )
    record = Record(
      self,
      "KLExtTypeAlias: %s -> %s[%s]" % (str(cpp_type_expr), kl_ext_name, kl_global_name),
      cpp_local_name,
      kl_global_name,
      self.type_mgr.get_dqti(cpp_type_expr).type_info,
      include_empty_ctor = False,
      include_copy_ctor = False,
      include_simple_ass_op = False,
      include_getters_setters = False,
      include_dtor = False,
      create_child_namespace = False,
      )
    self.ext.decls.append(record)
    self.cpp_type_expr_to_record[cpp_type_expr] = record
    return record

  def add_enum(
    self,
    cpp_local_name,
    values,
    kl_local_name = None,
    are_values_namespaced = False,
    ):
    assert isinstance(cpp_local_name, basestring)
    cur_value = 0
    clean_values = []
    for value in values:
      if isinstance(value, basestring):
        clean_values.append((value, cur_value))
      else:
        clean_values.append(value)
        cur_value = value[1]
      cur_value += 1
    cpp_type_expr = self.cpp_type_expr_parser.parse(cpp_local_name)
    assert isinstance(cpp_type_expr, Named)
    kl_local_name = self.maybe_generate_kl_local_name(kl_local_name, cpp_type_expr)
    kl_global_name = '_'.join(self.nested_kl_names + [kl_local_name])
    self.type_mgr.add_selector(
      EnumSelector(
        self.jinjenv,
        cpp_type_expr,
        kl_global_name,
        )
      )
    enum = Enum(
      self,
      "Enum: %s -> %s : %s" % (
        cpp_type_expr,
        kl_global_name,
        ", ".join(["%s=%d"%(val[0], val[1]) for val in clean_values]),
        ),
      self.type_mgr.get_dqti(cpp_type_expr).type_info,
      clean_values,
      are_values_namespaced = are_values_namespaced,
      )
    self.ext.decls.append(enum)
    return enum
