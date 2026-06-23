/**
 * @id local/yaml/parse-error
 * @name YAML parse error
 * @description Reports YAML parser errors in tracked configuration files.
 * @kind problem
 * @problem.severity warning
 * @precision very-high
 * @tags quality maintainability
 */

import semmle.python.Yaml

from YamlParseError error
select error, "YAML parse error: " + error.getMessage()
