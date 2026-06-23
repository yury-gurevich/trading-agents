/**
 * @id local/yaml/unresolved-include
 * @name Unresolved YAML include
 * @description Reports YAML !include directives whose target file cannot be resolved.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @tags quality maintainability
 */

import semmle.python.Yaml

from YamlInclude include
where not exists(include.eval())
select include, "Included YAML file '" + include.getValue() + "' could not be resolved."
