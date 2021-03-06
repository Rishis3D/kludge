{######################################################################}
{# Copyright (c) 2010-2016, Fabric Software Inc. All rights reserved. #}
{######################################################################}
{% extends "generate/decl/decl.fwds.cpp" %}
{% block body %}
{% if decl.is_simple %}
{% if decl.type_info.kl.name.base == 'CxxChar' %}
typedef char {{decl.type_info.edk.name}};

{% endif %}
{% else %}
typedef {{decl.type_info.lib.name}} {{decl.type_info.edk.name}};
{% endif %}

{% endblock body %}
