#ifndef __KL2EDK_AUTOGEN_{{ t.type_name }}__
#define __KL2EDK_AUTOGEN_{{ t.type_name }}__

#ifdef KL2EDK_INCLUDE_MESSAGES
  #pragma message ( "Including '{{ t.type_name }}.h'" )
#endif

////////////////////////////////////////////////////////////////
// THIS FILE IS AUTOMATICALLY GENERATED -- DO NOT MODIFY!!
////////////////////////////////////////////////////////////////
// Generated by kl2edk version {{ version_full }}
////////////////////////////////////////////////////////////////

#include <FabricEDK.h>
#if FABRIC_EDK_VERSION_MAJ != {{ version_maj }} || FABRIC_EDK_VERSION_MIN != {{ version_min }}
# error "This file needs to be rebuilt for the current EDK version!"
#endif

#include "global.h"

namespace Fabric { namespace EDK { namespace KL {

// KL interface '{{ t.type_name }}'
// Defined at {{ t.location }}

class {{ t.type_name }}
{
public:

  struct VTable
  {
{% for method in t.methods %}
  {% if manager.uses_returnval(method.ret_type_name) %}
    {{ method.ret_type_name }}
  {% else %}
    void
  {% endif %}
    (*{{ method.name }}_{{ method.hash() }})(
  {% if method.ret_type_name and not manager.uses_returnval(method.ret_type_name) %}
      Traits< {{ method.ret_type_name_cpp }} >::Result _result,
  {% endif %}
      ObjectCore const * const *objectCorePtr
  {% for param in method.params %}
,
      Traits< {{ param.type_name_cpp }} >::{{ param.usage_cpp }} {{ param.name -}}
    {% if loop.last %}

    {% endif %}
  {% endfor %}
    );
{% endfor %}
  };
  
  struct Bits
  {
    ObjectCore *objectCorePtr;
    SwapPtr<VTable const> const *vTableSwapPtrPtr;
  } *m_bits;
  
protected:
  
  friend struct Traits< {{ t.type_name }} >;
  static void ConstructEmpty( {{ t.type_name }} *self );
  static void ConstructCopy( {{ t.type_name }} *self, {{ t.type_name }} const *other );
  static void AssignCopy( {{ t.type_name }} *self, {{ t.type_name }} const *other );
  static void Destruct( {{ t.type_name }} *self );
  
public: 
  
  typedef {{ t.type_name }} &Result;
  typedef {{ t.type_name }} const &INParam;
  typedef {{ t.type_name }} &IOParam;
  typedef {{ t.type_name }} &OUTParam;
  
  {{ t.type_name }}();
  {{ t.type_name }}( {{ t.type_name }} const &that );
  {{ t.type_name }} &operator =( {{ t.type_name }} const &that );
  ~{{ t.type_name }}();
  void appendDesc( String::IOParam string ) const;
  bool isValid() const;
  operator bool() const;
  bool operator !() const;
  bool operator ==( INParam that );
  bool operator !=( INParam that );
  
{% for method in t.methods %}
  {% if method.ret_type_name %}
  {{ method.ret_type_name_cpp }}
  {% else %}
  void
  {% endif %}
  {{ method.name }}(
  {% for param in method.params %}
    {% if not loop.first %}
,
    {% endif %}
    Traits< {{ param.type_name_cpp }} >::{{ param.usage_cpp }} {{ param.name -}}
    {% if loop.last %}

    {% endif %}
  {% endfor %}
    ){% if method.usage == "in" %} const{% endif %};

{% endfor %}
};

inline void Traits<{{ t.type_name }}>::ConstructEmpty( {{ t.type_name }} &val )
{
  {{ t.type_name }}::ConstructEmpty( &val );
}
inline void Traits<{{ t.type_name }}>::ConstructCopy( {{ t.type_name }} &lhs, {{ t.type_name }} const &rhs )
{
  {{ t.type_name }}::ConstructCopy( &lhs, &rhs );
}
inline void Traits<{{ t.type_name }}>::AssignCopy( {{ t.type_name }} &lhs, {{ t.type_name }} const &rhs )
{
  {{ t.type_name }}::AssignCopy( &lhs, &rhs );
}
inline void Traits<{{ t.type_name }}>::Destruct( {{ t.type_name }} &val )
{
  {{ t.type_name }}::Destruct( &val );
}

}}}

#endif // __KL2EDK_AUTOGEN_{{ t.type_name }}__