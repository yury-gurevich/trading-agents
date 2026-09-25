"""Synthetic fixtures for the S231 point-in-time S&P 500 replay builder.

Agent: tooling
Role: provide non-copied Wikipedia-shaped HTML and tiny membership histories.
External I/O: none.
"""

from __future__ import annotations


def page_with_revision(body: str, revision: str = "987654321") -> str:
    return (
        "<html><head><script>var mw={config:{values:{wgRevisionId:"
        f"{revision}" + "}}};</script></head><body>"
        f"{body}</body></html>"
    )


def changes_table_fixture() -> str:
    table = """
    <table id="changes">
      <tr>
        <th rowspan="2">Date</th>
        <th colspan="2">Added</th>
        <th colspan="2">Removed</th>
        <th rowspan="2">Reason</th>
        <th rowspan="2">Refs</th>
      </tr>
      <tr><th>Ticker</th><th>Security</th><th>Ticker</th><th>Security</th></tr>
      <tr>
        <td>January 5, 2020</td><td>ABC |</td><td>Added Co</td>
        <td></td><td></td><td>added for test</td><td>[1]</td>
      </tr>
      <tr>
        <td>January 6, 2020</td><td></td><td></td>
        <td>DEF</td><td>Removed Co</td><td>removed for test</td>
      </tr>
    </table>
    """
    return page_with_revision(table)


def constituents_table_fixture() -> str:
    table = """
    <table id="not-the-table"><tr><td>NOPE</td></tr></table>
    <table id="constituents">
      <tr>
        <th>Symbol</th><th>Security</th><th>GICS Sector</th>
        <th>GICS Sub-Industry</th><th>Headquarters Location</th>
        <th>Date added</th><th>CIK</th><th>Founded</th>
      </tr>
      <tr>
        <td>BRK.B</td><td>Berkshire Example</td><td>Financials</td>
        <td>Holding</td><td>Omaha, Nebraska</td>
        <td>February 16, 2010</td><td>0001067983</td><td>1839</td>
      </tr>
    </table>
    """
    return page_with_revision(table, revision="123456789")


def universe_pages_fixture(symbols: tuple[str, ...] = ("AAA", "BBB")) -> dict[str, str]:
    rows = "\n".join(
        f"""
        <tr>
          <td>{symbol}</td><td>{symbol} Example</td><td>Sector</td>
          <td>Industry</td><td>Somewhere</td>
          <td>January 1, 2019</td><td>0001</td><td>2000</td>
        </tr>
        """
        for symbol in symbols
    )
    constituents = f"""
    <table id="constituents">
      <tr>
        <th>Symbol</th><th>Security</th><th>GICS Sector</th>
        <th>GICS Sub-Industry</th><th>Headquarters Location</th>
        <th>Date added</th><th>CIK</th><th>Founded</th>
      </tr>
      {rows}
    </table>
    """
    changes = """
    <table id="changes">
      <tr>
        <th rowspan="2">Date</th><th colspan="2">Added</th>
        <th colspan="2">Removed</th><th rowspan="2">Reason</th>
      </tr>
      <tr><th>Ticker</th><th>Security</th><th>Ticker</th><th>Security</th></tr>
    </table>
    """
    return {
        "constituents": page_with_revision(constituents, revision="111"),
        "changes": page_with_revision(changes, revision="222"),
    }
