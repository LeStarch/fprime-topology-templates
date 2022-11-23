# fprime-topology-templates

Uses Jinja2 to template FPP files. This allows for generating part(s) of topologies using templates. This can allow
replicating sets of subcomponents.

**Note:** this is unsupported prototype code. No support or assistance will be given for use at this time.

**Example: Topology FPP**
```fpp
module Ref {
    include "template_instances.instance1.fppt"

    topology Ref {
        include "template_connections.instance1.fppt"
    }
}
```

This example will create two FPP files that are included. The names will match those above. However, these files will
be created using template generation from `template_instances.fppt` and `template_connections.fppt` Jinja2 files
respectively. These outputs drop in directly via FPP includes.

## Copyright

```
Copyright 2022, by the California Institute of Technology.
ALL RIGHTS RESERVED.  United States Government Sponsorship
acknowledged.
```