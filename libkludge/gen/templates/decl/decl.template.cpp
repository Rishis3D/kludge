{######################################################################}
{# Copyright (c) 2010-2016, Fabric Software Inc. All rights reserved. #}
{######################################################################}

//////////////////////////////////////////////////////////////////////////////
//
// KLUDGE EDK
// Description: {{ decl.desc }}
{% if decl.location %}
// C++ Source Location: {{ decl.location }}
{% endif %}
//
//////////////////////////////////////////////////////////////////////////////
//

#include <{{ decl.include_filename }}>

{% block body %}
{% endblock body %}

//
//////////////////////////////////////////////////////////////////////////////