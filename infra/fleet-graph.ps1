# fleet-graph.ps1 — Render the live Aura fleet registry as an interactive graph
# and open it in the default browser. No Aura console login needed.
#
#   pwsh infra/fleet-graph.ps1
#
# Reads creds from the gitignored infra/aura-instance.local.json. The generated
# HTML bakes in only node labels/types (no secret), written to the temp dir.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$gen = Join-Path $PSScriptRoot "_fleet_graph_gen.local.py"
@'
import json, tempfile
from pathlib import Path
from neo4j import GraphDatabase

inst = json.load(open("infra/aura-instance.local.json", encoding="utf-8"))
driver = GraphDatabase.driver(
    "neo4j+s://8cf6d231.databases.neo4j.io", auth=("neo4j", inst["password"]))

COLORS = {"Session": "#f4c542", "AgentInstance": "#46c878",
          "CapabilityGrant": "#4aa3ff", "AgentDefinition": "#b07cff"}

def lbl(labels, p):
    if "AgentInstance" in labels: return p.get("agent_type", "agent")
    if "CapabilityGrant" in labels: return p.get("capability") or p.get("interface") or "grant"
    if "AgentDefinition" in labels: return p.get("name", "def")
    return labels[0] if labels else "?"

nodes, edges = [], []
with driver.session(database="neo4j") as s:
    for r in s.run("MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS p"):
        g = r["labels"][0] if r["labels"] else "?"
        nodes.append({"id": r["id"], "label": lbl(r["labels"], r["p"]),
                      "group": g, "color": COLORS.get(g, "#888")})
    for r in s.run("MATCH (a)-[rel]->(b) RETURN elementId(a) AS s, elementId(b) AS t, type(rel) AS ty"):
        edges.append({"from": r["s"], "to": r["t"], "label": r["ty"].lower()})
driver.close()

counts = {}
for n in nodes: counts[n["group"]] = counts.get(n["group"], 0) + 1
legend = "  ".join(f'<span style="color:{COLORS.get(k,"#888")}">&#9679; {k}: {v}</span>'
                   for k, v in sorted(counts.items()))

html = f"""<!doctype html><html><head><meta charset="utf-8"><title>trading-agents fleet</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>body{{margin:0;background:#0d1117;color:#c9d1d9;font-family:Segoe UI,system-ui,sans-serif}}
#h{{padding:10px 16px;font-size:18px;font-weight:600}}#l{{padding:0 16px 8px;font-size:13px}}
#net{{width:100vw;height:calc(100vh - 70px);border-top:1px solid #21262d}}</style></head>
<body><div id="h">TRADING-AGENTS FLEET &mdash; live registry (Aura, Sydney)</div>
<div id="l">{legend}</div><div id="net"></div><script>
const nodes=new vis.DataSet({json.dumps(nodes)});
const edges=new vis.DataSet({json.dumps(edges)});
new vis.Network(document.getElementById('net'),{{nodes,edges}},{{
  nodes:{{shape:'dot',size:16,font:{{color:'#c9d1d9',size:14}}}},
  edges:{{color:'#30363d',font:{{color:'#8b949e',size:10}},arrows:'to',smooth:true}},
  physics:{{stabilization:false,barnesHut:{{gravitationalConstant:-3000,springLength:120}}}}}});
</script></body></html>"""

out = Path(tempfile.gettempdir()) / "trading-agents-fleet.html"
out.write_text(html, encoding="utf-8")
print(out)
'@ | Out-File $gen -Encoding utf8

$path = uv run python $gen 2>$null
Remove-Item $gen -Force -ErrorAction SilentlyContinue
if ($path) {
  Write-Host "Fleet graph: $path" -ForegroundColor Green
  Start-Process $path
} else {
  Write-Host "No data (is Aura running? pwsh infra/aura.ps1 status)" -ForegroundColor Yellow
}
