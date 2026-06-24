/**
 * @name Untrusted URL passed to urlopen (SSRF / URL injection)
 * @description External input (MCP tool args, CLI arguments, environment
 *              variables) flows into urllib.request.urlopen without being
 *              validated against an allow-list of hosts. A crafted value can
 *              redirect the fetch to an attacker-controlled endpoint (SSRF) or
 *              smuggle a query parameter (URL injection).
 * @kind path-problem
 * @id local/py/untrusted-url-to-urlopen
 * @problem.severity warning
 * @precision high
 * @tags security external/cve-injection
 */

import python
import semmle.python.dataflow.new.DataFlow
import semmle.python.dataflow.new.TaintTracking
import UntrustedUrlFlow::PathGraph

// ---------------------------------------------------------------------------
// Sources - places where untrusted data enters the trading-agents process.
// ---------------------------------------------------------------------------

/** A subscript or `.get()` call on a dict named `args` (MCP tool arguments). */
predicate argsAccess(DataFlow::Node node) {
  // args["text"]  /  args.get("text")
  exists(Subscript sub |
    sub.getObject().(Name).getId() = "args" and
    node = DataFlow::exprNode(sub)
  )
  or
  exists(Call c |
    c.getFunc().(Attribute).getName() = "get" and
    c.getFunc().(Attribute).getObject().(Name).getId() = "args" and
    node = DataFlow::exprNode(c)
  )
}

/** os.environ.get(...) / os.environ[...] - env-derived config. */
predicate environAccess(DataFlow::Node node) {
  exists(Call c |
    c.getFunc().(Attribute).getName() = "get" and
    c.getFunc().(Attribute).getObject().(Attribute).getName() = "environ" and
    node = DataFlow::exprNode(c)
  )
  or
  exists(Subscript sub |
    sub.getObject().(Attribute).getName() = "environ" and
    node = DataFlow::exprNode(sub)
  )
}

/** sys.argv[i] - CLI surface. */
predicate argvAccess(DataFlow::Node node) {
  exists(Subscript sub |
    sub.getObject().(Name).getId() = "argv" and
    sub.getObject().(Name).getScope().getEnclosingModule().getName() = "sys" and
    node = DataFlow::exprNode(sub)
  )
}

/** Attribute access on an `args` / `parsed` argparse Namespace, e.g. args.ticker. */
predicate argparseAccess(DataFlow::Node node) {
  exists(Attribute attr |
    attr.getObject().(Name).getId() in ["args", "parsed", "namespace"] and
    node = DataFlow::exprNode(attr)
  )
}

// ---------------------------------------------------------------------------
// Sink - urllib.request.urlopen(<url>); the first positional argument.
// ---------------------------------------------------------------------------

predicate urlopenSink(DataFlow::Node sink) {
  exists(Call c |
    c.getFunc().(Attribute).getName() = "urlopen" and
    (
      // urllib.request.urlopen(...)
      c.getFunc().(Attribute).getObject().(Attribute).getName() = "request" or
      // request.urlopen(...)  after `from urllib import request`
      c.getFunc().(Attribute).getObject().(Name).getId() = "request"
    ) and
    sink = DataFlow::exprNode(c.getArg(0))
  )
}

// ---------------------------------------------------------------------------
// Barrier - a string-prefix / regex host allow-list check dominating the sink.
// ---------------------------------------------------------------------------

predicate allowListBarrier(DataFlow::Node node) {
  // `url.startswith("https://api.example.com")`
  exists(Call startswith |
    startswith.getFunc().(Attribute).getName() = "startswith" and
    startswith.getArg(0) instanceof StringLiteral and
    node = DataFlow::exprNode(startswith.getFunc().(Attribute).getObject())
  )
  or
  // `re.match(r"^https://...", url)`  /  re.fullmatch / re.search
  exists(Call reMatch |
    reMatch.getFunc().(Attribute).getName() in ["match", "fullmatch", "search"] and
    reMatch.getFunc().(Attribute).getObject().(Name).getId() = "re" and
    node = DataFlow::exprNode(reMatch.getArg(1))
  )
  or
  // `int(...)` cast on a port number is not a URL taint path.
  exists(Call c |
    c.getFunc().(Name).getId() = "int" and
    node = DataFlow::exprNode(c)
  )
}

// ---------------------------------------------------------------------------
// Taint configuration - wire sources, sinks, and barriers together.
// ---------------------------------------------------------------------------

module UntrustedUrlConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    argsAccess(source) or
    environAccess(source) or
    argvAccess(source) or
    argparseAccess(source)
  }

  predicate isSink(DataFlow::Node sink) {
    urlopenSink(sink)
  }

  predicate isBarrier(DataFlow::Node node) {
    allowListBarrier(node)
  }
}

module UntrustedUrlFlow = TaintTracking::Global<UntrustedUrlConfig>;

// ---------------------------------------------------------------------------
// Query - emit every source -> sink path.
// ---------------------------------------------------------------------------

from UntrustedUrlFlow::PathNode source, UntrustedUrlFlow::PathNode sink
where UntrustedUrlFlow::flowPath(source, sink)
select sink.getNode(), source, sink,
  "Untrusted $@ flows into urlopen - possible SSRF / URL injection.",
  source.getNode(), "untrusted input"
