#
# Copyright (c) 2010-2016, Fabric Software Inc. All rights reserved.
#

import inspect, hashlib, abc
from decl import Decl
from test import Test
from libkludge.member_access import MemberAccess
from this_access import ThisAccess
from massage import *
from libkludge.cpp_type_expr_parser import Void, DirQual, directions, qualifiers
from libkludge.value_name import this_cpp_value_name
from libkludge.this_codec import ThisCodec
from libkludge.result_codec import ResultCodec
from libkludge.param_codec import ParamCodec
from libkludge.dir_qual_type_info import DirQualTypeInfo
from libkludge.util import clean_comment

class Methodlike(object):

  def __init__(self, record):
    self.record = record
    self.comments = []
  
  @property
  def ext(self):
    return self.record.ext

  def add_test(self, kl, out):
    self.ext.add_test(self.get_test_name(), kl, out)
    return self

  def add_comment(self, comment):
    self.comments.append(clean_comment(comment))
    return self

  @abc.abstractmethod
  def get_test_name():
    pass

class Ctor(Methodlike):

  def __init__(
    self,
    record,
    params,
    ):
    Methodlike.__init__(self, record)
    self.base_edk_symbol_name = record.kl_global_name + '__ctor'
    self.params = [param.gen_codec(index, record.resolve_dqti) for index, param in enumerate(params)]
  
  @property
  def edk_symbol_name(self):
    h = hashlib.md5()
    h.update(self.base_edk_symbol_name)
    for param in self.params:
      h.update(param.type_info.edk.name)
    return "_".join([self.ext.name, self.base_edk_symbol_name, h.hexdigest()])

  def get_test_name(self):
    return self.base_edk_symbol_name    

  def get_this(self, type_info):
    return self.record.get_this(type_info, True)

class Method(Methodlike):

  def __init__(
    self,
    record,
    cpp_name,
    returns,
    params,
    this_access,
    ):
    Methodlike.__init__(self, record)
    self.base_edk_symbol_name = record.kl_global_name + '__meth_' + cpp_name
    self.cpp_name = cpp_name
    self.result = ResultCodec(record.resolve_dqti(returns))
    self.params = [param.gen_codec(index, record.resolve_dqti) for index, param in enumerate(params)]
    self.this_access = this_access
    self.is_const = self.this_access == ThisAccess.const
    self.is_mutable = self.this_access == ThisAccess.mutable
    self.is_static = self.this_access == ThisAccess.static

  @property
  def kl_name(self):
    return self.cpp_name

  @property
  def this_access_suffix(self):
    if self.this_access == ThisAccess.const:
      return '?'
    elif self.this_access == ThisAccess.mutable:
      return '!'
    else:
      assert False
  
  @property
  def edk_symbol_name(self):
    h = hashlib.md5()
    h.update(self.base_edk_symbol_name)
    for param in self.params:
      h.update(param.type_info.edk.name)
    return "_".join([self.ext.name, self.base_edk_symbol_name, h.hexdigest()])

  def get_test_name(self):
    return self.base_edk_symbol_name

  def get_this(self, type_info):
    assert this_access != ThisAccess.static
    return self.record.get_this(type_info, this_access == ThisAccess.mutable)

class UniOp(Methodlike):

  op_to_edk_op = {
    "++": 'INC',
    "--": 'DEC',
  }

  def __init__(
    self,
    record,
    op,
    kl_method_name,
    result_cpp_type_name,
    ):
    Methodlike.__init__(self, record)
    self.resolve_cpp_type_expr = record.resolve_cpp_type_expr
    self.base_edk_symbol_name = record.kl_global_name + '__uni_op_'+self.op_to_edk_op[op]
    assert isinstance(kl_method_name, basestring)
    self.kl_method_name = kl_method_name
    self.op = op
    assert isinstance(result_cpp_type_name, basestring)
    self.result = ResultCodec(
      self.ext.type_mgr.get_dqti(
        self.resolve_cpp_type_expr(result_cpp_type_name)
        )
      )

  @property
  def ext(self):
    return self.record.ext
  
  @property
  def edk_symbol_name(self):
    h = hashlib.md5()
    h.update(self.base_edk_symbol_name)
    return "_".join([self.ext.name, self.base_edk_symbol_name, h.hexdigest()])

  def get_test_name(self):
    return self.base_edk_symbol_name

  def get_this(self, type_info):
    return self.record.get_this(type_info, True)

class BinOp(Methodlike):

  op_to_edk_op = {
    "+": 'ADD',
    "-": 'SUB',
    "*": 'MUL',
    "/": 'DIV',
    "%": 'MOD',
    "==": 'EQ',
    "!=": 'NE',
    "<": 'LT',
    "<=": 'LE',
    ">": 'GT',
    ">=": 'GE',
    "===": 'EX_EQ',
    "!==": 'EX_NE',
    "|": 'BIT_OR',
    "&": 'BIT_AND',
    "^": 'BIT_XOR',
    "<<": 'SHL',
    ">>": 'SHR',
  }

  def __init__(
    self,
    record,
    result_type,
    op,
    lhs_param_name,
    lhs_param_type,
    rhs_param_name,
    rhs_param_type,
    ):
    Methodlike.__init__(self, record)
    self.resolve_cpp_type_expr = record.resolve_cpp_type_expr
    self.base_edk_symbol_name = record.kl_global_name + '__bin_op_'+self.op_to_edk_op[op]
    self.result = ResultCodec(
      self.ext.type_mgr.get_dqti(
        self.resolve_cpp_type_expr(result_type)
        )
      )
    self.op = op
    self.params = [
      ParamCodec(
        self.ext.type_mgr.get_dqti(
          self.resolve_cpp_type_expr(lhs_param_type)
          ),
        lhs_param_name
        ),
      ParamCodec(
        self.ext.type_mgr.get_dqti(
          self.resolve_cpp_type_expr(rhs_param_type)
          ),
        rhs_param_name
        ),
      ]

  @property
  def ext(self):
    return self.record.ext
  
  @property
  def edk_symbol_name(self):
    h = hashlib.md5()
    h.update(self.base_edk_symbol_name)
    for param in self.params:
      h.update(param.type_info.edk.name)
    return "_".join([self.ext.name, self.base_edk_symbol_name, h.hexdigest()])

  def get_test_name(self):
    return self.base_edk_symbol_name

class AssOp(Methodlike):

  op_to_edk_op = {
    "=": 'SIMPLE',
    "+=": 'ADD',
    "-=": 'SUB',
    "*=": 'MUL',
    "/=": 'DIV',
    "%=": 'MOD',
    "|=": 'BIT_OR',
    "&=": 'BIT_AND',
    "^=": 'BIT_XOR',
    "<<=": 'SHL',
    ">>=": 'SHR',
  }

  def __init__(
    self,
    record,
    op,
    param_type,
    param_name,
    ):
    Methodlike.__init__(self, record)
    self.resolve_cpp_type_expr = record.resolve_cpp_type_expr
    self.base_edk_symbol_name = record.kl_global_name + '__ass_op_' + self.op_to_edk_op[op]
    self.op = op
    self.params = [
      ParamCodec(
        self.ext.type_mgr.get_dqti(
          self.resolve_cpp_type_expr(param_type)
          ),
        param_name
        ),
      ]

  @property
  def ext(self):
    return self.record.ext
  
  @property
  def edk_symbol_name(self):
    h = hashlib.md5()
    h.update(self.base_edk_symbol_name)
    for param in self.params:
      h.update(param.type_info.edk.name)
    return "_".join([self.ext.name, self.base_edk_symbol_name, h.hexdigest()])

  def get_test_name(self):
    return self.base_edk_symbol_name

  def get_this(self, type_info):
    return self.record.get_this(type_info, True)

class Cast(Methodlike):

  def __init__(
    self,
    record,
    dst_cpp_type_name,
    ):
    Methodlike.__init__(self, record)
    self.resolve_cpp_type_expr = record.resolve_cpp_type_expr
    assert isinstance(dst_cpp_type_name, basestring)
    this_dqti = self.ext.type_mgr.get_dqti(
      self.resolve_cpp_type_expr(dst_cpp_type_name)
      )
    self.base_edk_symbol_name = this_dqti.type_info.kl.name.compound + '__cast'
    self.this = ThisCodec(
      this_dqti.type_info,
      [],
      True, # is_mutable
      )
    self.params = [
      ParamCodec(
        DirQualTypeInfo(
          DirQual(directions.Reference, qualifiers.Const),
          record.const_this.type_info,
          ),
        "that"
        ),
      ]

  @property
  def ext(self):
    return self.record.ext
  
  @property
  def edk_symbol_name(self):
    h = hashlib.md5()
    h.update(self.base_edk_symbol_name)
    for param in self.params:
      h.update(param.type_info.edk.name)
    return "_".join([self.ext.name, self.base_edk_symbol_name, h.hexdigest()])

  def get_test_name(self):
    return self.base_edk_symbol_name

class Record(Decl):

  def __init__(
    self,
    parent_namespace,
    record_desc,
    kl_local_name,
    extends = None,
    include_empty_ctor = True,
    include_copy_ctor = True,
    include_simple_ass_op = True,
    include_getters_setters = True,
    include_dtor = True,
    forbid_copy = False,
    child_namespace_component = None,
    ):
    Decl.__init__(self, parent_namespace)
    self.record_desc = record_desc

    if child_namespace_component:
      self.namespace = parent_namespace.create_child(child_namespace_component, kl_local_name)
      for namespace_method in inspect.getmembers(
        self.namespace,
        predicate = inspect.ismethod,
        ):
        if namespace_method[0] not in ['add_func']:
          setattr(self, namespace_method[0], namespace_method[1])
    else:
      self.namespace = parent_namespace
    for method_name in ['resolve_cpp_type_expr', 'resolve_dqti']:
      setattr(self, method_name, getattr(self.namespace, method_name))

    self.comments = []
    self.members = []
    self.ctors = []
    self.methods = []
    self.uni_ops = []
    self.bin_ops = []
    self.ass_ops = []
    self.casts = []
    self.deref_kl_method_name = None
    self.deref_result = None

    self.kl_local_name = kl_local_name
    self.this_value_name = this_cpp_value_name
    self.extends = extends
    self.default_access = MemberAccess.public
    self.include_empty_ctor = include_empty_ctor
    self.include_copy_ctor = include_copy_ctor
    self.include_simple_ass_op = include_simple_ass_op
    self.include_getters_setters = include_getters_setters
    self.include_dtor = include_dtor
    self.forbid_copy = forbid_copy
    self.get_ind_op_result = None
    self.get_ind_op_params = None
    self.set_ind_op_params = None

  def get_this(self, type_info, is_mutable):
    return ThisCodec(type_info, is_mutable)

  def get_const_this(self, type_info):
    return self.get_this(type_info, False)
    
  def get_mutable_this(self, type_info):
    return self.get_this(type_info, True)
    
  def get_copy_param(self, type_info):
    return ParamCodec(
      DirQualTypeInfo(DirQual(directions.Direct, qualifiers.Unqualified), type_info),
      "that"
      )

  def get_desc(self):
    return "Record"
  
  def resolve_cpp_type_expr(self, cpp_type_name):
    return self.namespace.resolve_cpp_type_expr(cpp_type_name)

  def add_comment(self, comment):
    self.comments.append(clean_comment(comment))
    print str(self.comments)
    return self

  def set_default_access(self, access):
    self.default_access = access

  class Member(object):

    def __init__(self, record, cpp_name, dqti, getter_kl_name, setter_kl_name, access):
      self.record = record
      self.cpp_name = cpp_name
      self.kl_name = cpp_name
      self.type_info = dqti.type_info
      self.result = ResultCodec(dqti)
      self.param = ParamCodec(dqti, cpp_name)
      self.getter_kl_name = getter_kl_name
      if not self.getter_kl_name is None and self.getter_kl_name == '':
        self.getter_kl_name = 'get_' + cpp_name
      self.setter_kl_name = setter_kl_name
      if not self.setter_kl_name is None and self.setter_kl_name == '':
        self.setter_kl_name = 'set_' + cpp_name
      self.access = access

    def has_getter(self):
      return self.getter_kl_name is not None

    def has_setter(self):
      return self.setter_kl_name is not None

    def is_public(self):
      return self.access == MemberAccess.public
    
  def add_member(self, cpp_name, cpp_type_name, getter='', setter='', access=None):
    if access is None:
      access = self.default_access
    cpp_type_expr = self.resolve_cpp_type_expr(cpp_type_name)
    dqti = self.ext.type_mgr.get_dqti(cpp_type_expr)
    member = self.Member(self, cpp_name, dqti, getter, setter, access=access)
    self.members.append(member)
    return self
  
  def add_ctor(self, params=[], opt_params=[]):
    params = massage_params(params)
    opt_params = massage_params(opt_params)

    if len(params) == 0:
      self.include_empty_ctor = False

    result = None
    for i in range(0, len(opt_params)+1):
      ctor = Ctor(self, params + opt_params[0:i])
      self.ctors.append(ctor)
      if not result:
        result = ctor
    return result

  def add_method(
    self,
    name,
    returns = None,
    params = [],
    opt_params = [],
    this_access = ThisAccess.const,
    ):
    assert isinstance(name, basestring)

    returns = massage_returns(returns)
    params = massage_params(params)
    opt_params = massage_params(opt_params)

    result = None
    for i in range(0, len(opt_params)+1):
      method = Method(self, name, returns, params + opt_params[0:i], this_access)
      self.methods.append(method)
      if not result:
        result = method
    return result

  def add_const_method(self, name, returns=None, params=[], opt_params=[]):
    return self.add_method(name, returns, params, opt_params, ThisAccess.const)

  def add_mutable_method(self, name, returns=None, params=[], opt_params=[]):
    return self.add_method(name, returns, params, opt_params, ThisAccess.mutable)

  def add_static_method(self, name, returns=None, params=[], opt_params=[]):
    return self.add_method(name, returns, params, opt_params, ThisAccess.static)
  
  def add_uni_op(
    self,
    op,
    kl_method_name,
    returns,
    ):
    uni_op = UniOp(
      self,
      op,
      kl_method_name,
      returns,
      )
    self.uni_ops.append(uni_op)
    return uni_op
  
  def add_bin_op(
    self,
    op,
    returns='bool',
    params=None,
    ):
    if not params:
      params = [self.this_type_info.lib.name.compound + ' const &', self.this_type_info.lib.name.compound + ' const &']
    assert len(params) == 2
    bin_op = BinOp(
      self,
      result_type=returns,
      op=op,
      lhs_param_name='lhs',
      lhs_param_type=params[0],
      rhs_param_name='rhs',
      rhs_param_type=params[1],
      )
    self.bin_ops.append(bin_op)
    return bin_op
  
  def add_ass_op(
    self,
    op,
    params,
    ):
    assert len(params) == 1
    ass_op = AssOp(
      self,
      op=op,
      param_name='arg',
      param_type=params[0],
      )
    self.ass_ops.append(ass_op)
    return ass_op
      
  def add_cast(
    self,
    dst,
    ):
    cast = Cast(self, dst)
    self.casts.append(cast)
    return cast

  def add_get_ind_op(
    self,
    value_cpp_type_name,
    this_access = ThisAccess.const
    ):
    self.get_ind_op_result = ResultCodec(
      self.ext.type_mgr.get_dqti(
        self.resolve_cpp_type_expr(value_cpp_type_name)
        )
      )
    self.get_ind_op_params = [
      ParamCodec(
        self.ext.type_mgr.get_dqti(
          self.resolve_cpp_type_expr('size_t')
          ),
        'index'
        ),
      ]
    self.get_ind_op_this_access = this_access
    return self

  def get_get_ind_op_this(self, type_info):
    return self.get_this(type_info, self.get_ind_op_this_access == ThisAccess.mutable)

  def add_set_ind_op(
    self,
    value_cpp_type_name,
    this_access = ThisAccess.mutable
    ):
    self.set_ind_op_params = [
      ParamCodec(
        self.ext.type_mgr.get_dqti(
          self.resolve_cpp_type_expr('size_t')
          ),
        'index'
        ),
      ParamCodec(
        self.ext.type_mgr.get_dqti(
          self.resolve_cpp_type_expr(value_cpp_type_name)
          ),
        'value'
        ),
      ]
    self.set_ind_op_this_access = this_access
    return self

  def get_set_ind_op_this(self, type_info):
    return self.get_this(type_info, self.set_ind_op_this_access == ThisAccess.mutable)

  def add_deref(
    self,
    kl_method_name,
    returns,
    this_access = ThisAccess.const
    ):
    assert not self.deref_kl_method_name
    assert isinstance(kl_method_name, basestring)
    self.deref_kl_method_name = kl_method_name
    assert isinstance(returns, basestring)
    self.deref_result = ResultCodec(
      self.ext.type_mgr.get_dqti(
        self.resolve_cpp_type_expr(returns)
        )
      )
    self.deref_this_access = this_access
    return self
    
  @property
  def empty_ctor_edk_symbol_name(self):
    base_edk_symbol_name = self.kl_global_name + '__empty_ctor'
    h = hashlib.md5()
    h.update(base_edk_symbol_name)
    return "_".join([self.ext.name, base_edk_symbol_name, h.hexdigest()])
    
  @property
  def copy_ctor_edk_symbol_name(self):
    base_edk_symbol_name = self.kl_global_name + '__copy_ctor'
    h = hashlib.md5()
    h.update(base_edk_symbol_name)
    return "_".join([self.ext.name, base_edk_symbol_name, h.hexdigest()])
    
  @property
  def simple_ass_op_edk_symbol_name(self):
    base_edk_symbol_name = self.kl_global_name + '__simple_ass_op'
    h = hashlib.md5()
    h.update(base_edk_symbol_name)
    return "_".join([self.ext.name, base_edk_symbol_name, h.hexdigest()])
    
  @property
  def deref_edk_symbol_name(self):
    base_edk_symbol_name = self.kl_global_name + '__deref'
    h = hashlib.md5()
    h.update(base_edk_symbol_name)
    return "_".join([self.ext.name, base_edk_symbol_name, h.hexdigest()])

  @property
  def get_ind_op_edk_symbol_name(self):
    base_edk_symbol_name = self.kl_global_name + '__get_ind_op'
    h = hashlib.md5()
    h.update(base_edk_symbol_name)
    return "_".join([self.ext.name, base_edk_symbol_name, h.hexdigest()])

  @property
  def set_ind_op_edk_symbol_name(self):
    base_edk_symbol_name = self.kl_global_name + '__set_ind_op'
    h = hashlib.md5()
    h.update(base_edk_symbol_name)
    return "_".join([self.ext.name, base_edk_symbol_name, h.hexdigest()])
  
  @property
  def dtor_edk_symbol_name(self):
    base_edk_symbol_name = self.kl_global_name + '__dtor'
    h = hashlib.md5()
    h.update(base_edk_symbol_name)
    return "_".join([self.ext.name, base_edk_symbol_name, h.hexdigest()])

  def get_test_name(self):
    return self.kl_global_name

  @property
  def kl_global_name(self):
    return '_'.join(self.namespace.nested_kl_names)

  def get_template_path(self):
    return 'generate/record/record'

  def get_template_aliases(self):
    return ['record']

  def has_ctors(self):
    return len(self.ctors) > 0

  def has_methods(self):
    return len(self.methods) > 0

  def has_uni_ops(self):
    return len(self.uni_ops) > 0

  def has_bin_ops(self):
    return len(self.bin_ops) > 0

  def has_ass_ops(self):
    return len(self.ass_ops) > 0

  def has_casts(self):
    return len(self.casts) > 0
