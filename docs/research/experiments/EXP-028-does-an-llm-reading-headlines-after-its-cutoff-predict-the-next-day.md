# EXP-028 — Does an LLM reading headlines published after its training cutoff predict the next day's return?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `74d791f6`) · **COMPLETE 2026-10-24: NONE. The model reads
news correctly (after-close headlines: good +0.38 %, bad −1.06 % overnight), but the move is priced
before the next open; the fleet's trade loses (net −0.12 % a day at 5 bps).** $1.39 of OpenAI spend.
**Decision / origin:** [DL-317](../../design-log.md) Amendments 4–5; the operator, 2026-10-24: *"let's
see if it works"*, then *"yes, i approve $20 for OpenAI"* · **Cost:** about $1.40 of OpenAI Batch spend
(estimate from token counts), capped at $20 by the script.

## 1. Why we needed this experiment

**The decision that waits.** The operator keeps the fleet running and asked whether an LLM can find
what the price-based tools could not (DL-317 Amendment 4). Training one on our data was ruled out
(lookahead, no signal, a tiny trade record). The one LLM result with evidence after a model's cutoff is
Lopez-Lira and Tang's: ChatGPT-3.5's reading of a headline predicted the next day's return, and a 2026
paper found the signal still significant on 2024 news after the cutoff ([R011](../where-an-edge-can-exist/INDEX.md)).

**What it also answers.** The operator asked whether the fleet's entry (decide at night, buy at the next
open) and the cost of one-day trades can be changed. The same labels, read against four windows of
return, show where any effect sits: overnight, the next day, from the close, or from the open after an
early read.

**Why this model.** Every GPT-3.5 model is retired on the fleet's key *[measured 2026-10-24: 404 on
`gpt-3.5-turbo-0125`, `-1106`, `-16k`, `-instruct`]*; `gpt-4o-mini-2024-07-18`, trained on data to
October 2023, is served. Scoring from 2024-01-01 leaves two months of margin after its cutoff: it cannot
have read any headline it scores, or the prices that followed.

## 2. Hypothesis

**The statistic.** For each decision session *t* with at least one stock the model calls good, P(*t*)
is the mean over those stocks of their **next-day excess return**: from the open of *t* + 1 to its
close, minus the equal-weighted mean of all S&P 500 members over the same hours. **Net** = P(*t*) − 2 ×
5 bps (buy at the open, sell at the close). This is what the fleet can capture as it trades today.

- **H1 — EDGE.** The mean of net P(*t*) over sessions is above 0 with the lower bound of its 95 %
  interval above 0, and the mean is above 0 in each half of the sessions.
- **H0 — NONE.** Otherwise.

**The interval.** Stationary block bootstrap over sessions, mean block 20, 5,000 resamples, seed 0.

**Why this bar.** One model, one primary window: no correction. 5 bps a side is a realistic cost for
liquid S&P 500 names with limit orders, and the cheapest the project has assumed; at 25 bps a one-day
trade needs 0.5 % a day, a bar no published headline signal reaches. Both costs above are reported.

## 3. Data

| Input | Span | Where |
| --- | --- | --- |
| Benzinga headlines (Alpaca news archive, EXP-024) | created 2024-01-01 → 2026-09-24 | OneDrive `trading-agents-data/news-alpaca/` |
| The headline set (`exp028_build.py`): a single symbol, an S&P 500 member on the decision session, de-duplicated by symbol, session and text | **152,728** headlines, 555 symbols, 685 sessions; by arrival: market hours 78,550, before the open 50,608, after the close 19,201, overnight or non-session days 4,369 | kit `headlines.csv.gz` |
| Company names | Alpaca's asset list (150,380 named; the rest use the ticker) | kit |
| S235 cache bars (`adjustment=all`) and membership | to 2026-09-25 | OneDrive `trading-agents-data/` |

The kit is OneDrive `trading-agents-data/exp028-2026-10-24/`.

## 4. Tools and setup

- **Machine** as EXP-026. Python 3.13.2, pandas 3.0.6, numpy 2.5.3, openai 2.49.0, tiktoken 0.13.0.
- **Model** `gpt-4o-mini-2024-07-18`, temperature 0, at most 2 output tokens, via the Batch API.
- **Random seed** 0. **Cost cap** $20 (the operator's), enforced from the batches' recorded usage.

## 5. How it was conducted

1. **Decision session.** A headline belongs to the fleet's nightly run at 18:30 ET: to session *t* if
   it arrives on *t* by 18:30 ET, else to the next session. Its arrival class: market hours (09:30–16:00
   on *t*), after the close (16:00–18:30 on *t*), before the open (on *t* before 09:30), overnight
   (after 18:30 the evening before, or a non-session day).
2. **The prompt** is Lopez-Lira and Tang's, verbatim in Appendix P; one headline per request.
3. **The label.** The first word: YES → +1, NO → −1, anything else 0. Per stock and session, the mean
   of its headlines' labels: **good** above 0, **bad** below 0.
4. **Returns** from the cache, each minus the members' equal-weighted mean over the same window:
   **DAY** open(*t*+1) → close(*t*+1) (primary); **OVN** close(*t*) → open(*t*+1); **CC** close(*t*) →
   close(*t*+1); **DAY0** open(*t*) → close(*t*), for headlines that arrived before *t*'s open (what an
   early-morning read could buy at *t*'s open).
5. **Pilot (before the freeze):** 100 live requests: 53 YES, 28 UNKNOWN, 19 NO, every answer parsed.
6. **Reported, not barred:** the good-minus-bad spread for DAY, OVN, CC and DAY0; good alone and bad
   alone; each by arrival class and by year; at 10 and 25 bps a side; hit rates; label shares.
7. **Failure handling.** No verdict if under 95 % of answers parse or over 1 % of requests fail
   (failures re-run once first).

**What this cannot claim, stated before the result.** OVN measures the move an after-hours or
closing-auction buyer would face, not what they would be filled at (extended-hours prices are not in
daily bars). One model and one prompt; a NONE verdict says this reading of headlines did not carry,
not that no LLM could. The S&P 500 is where the literature finds the effect weakest.

## 6. Results

All MEASURED from the frozen scripts (Appendix R). **Labels:** 152,728 answers, 0 failed, 100 % parsed:
YES 79,512 (52 %), NO 31,052 (20 %), other 42,164 (28 %). 81,628 stock-sessions (44,114 good, 14,482
bad) on 685 sessions.

**Primary (the fleet as it trades): NONE.** The good stocks' next-day excess, open → close, averaged
**−0.017 %** a session gross; net of 5 bps a side **−0.117 %** [−0.146, −0.091], halves −0.112 % and
−0.122 %, positive on 33 % of sessions. At 10 bps −0.217 %; at 25 bps −0.517 %. By year, gross: 2024
−0.024 %, 2025 +0.002 %, 2026 −0.034 %.

**Where the return sits** (reported, not barred: good minus bad, per session, 95 % interval):

| Headlines arriving | Overnight close(t) → open(t+1) | Next day open → close | Close → close |
| --- | --- | --- | --- |
| all | **+0.204 %** [+0.168, +0.241] (good +0.066, bad −0.137) | −0.065 % [−0.115, −0.013] | +0.138 % [+0.073, +0.203] |
| in market hours (78,550) | +0.083 % [+0.052, +0.114] (good +0.044, bad −0.039) | −0.067 % [−0.130, −0.007] | +0.015 % [−0.054, +0.082] |
| **after the close, by 18:30 ET (19,201)** | **+1.433 %** [+1.179, +1.696] (**good +0.376, bad −1.059**) | +0.020 % [−0.138, +0.188] | +1.448 % [+1.177, +1.739] |
| before the open (50,608) | −0.021 % [−0.063, +0.021] | −0.035 % [−0.092, +0.019] | −0.056 % [−0.116, +0.006] |
| overnight or non-session days (4,369) | −0.031 % [−0.245, +0.178] | −0.124 % [−0.322, +0.080] | −0.153 % [−0.466, +0.157] |

An early read of the before-the-open headlines, bought at that session's open and sold at its close,
earns +0.017 % [−0.062, +0.101] good minus bad.

## 7. Conclusions

1. **As the fleet trades, the LLM's reading of headlines loses money.** Buying the good-news stocks at
   the next open earns nothing before costs and −0.12 % a day after the cheapest cost assumed. H0.
2. **The model reads news correctly, and the market reads it first.** After-close headlines it called
   good rose 0.38 % by the next open and those it called bad fell 1.06 %: a spread of 1.4 % that is
   real and large. But all of it is in the overnight gap; from the next open, nothing is left.
3. **Earlier entries the fleet could reach do not help.** Reading the morning's headlines and buying at
   the open earns nothing; buying market-hours good news at that day's close catches a +0.04 % next
   morning, too thin for a daily round trip.
4. **The only place left is the minutes after an after-close headline,** in after-hours trading
   (Alpaca accepts extended-hours limit orders, 16:00–20:00 ET). Whether any of the 1.4 % is still
   there a few minutes after the headline, when an LLM could have read it and an order reached the
   market, is not in daily bars. It is the follow-up this result names.

## 8. Recommended code changes, and how to implement them

**None to the fleet now.** The follow-up is a measurement, not a build: with minute bars that include
extended hours, measure how much of the after-close move remains 1, 5, 15 and 60 minutes after each
headline (a planner's $0 experiment). Only if a meaningful share remains after realistic latency and
after-hours spreads would an event-driven news reader be worth a sprint.

## Appendix P — Pre-registration (frozen)

- Model `gpt-4o-mini-2024-07-18`; temperature 0; `max_tokens` 2; one user message:

```text
Forget all your previous instructions. Pretend you are a financial expert. You are a financial expert with stock recommendation experience. Answer "YES" if good news, "NO" if bad news, or "UNKNOWN" if uncertain in the first line. Then elaborate with one short and concise sentence on the next line. Is this headline good or bad for the stock price of {name} in the short term?

Headline: {headline}
```

- Headlines 2024-01-01 → 2026-09-24, one symbol, an S&P 500 member on the decision session; decision
  session by the 18:30 ET rule; labels YES +1, NO −1, else 0; good above 0, bad below 0.
- **Primary:** mean over sessions of [mean next-day (open → close) excess return of the good stocks −
  10 bps]; EDGE if its 95 % interval (stationary block bootstrap, block 20, 5,000, seed 0) is above 0
  and both halves' means are above 0; else NONE.
- Secondary as section 5.6. Cap $20.

## Appendix R — Run record

- 2026-10-24, planner. Probe: every GPT-3.5 model returned 404 (retired); `gpt-4o-mini-2024-07-18`
  answered. Build (`exp028_build.py`, START 2024-01-01 after the switch): 152,728 headlines; estimate
  $1.40. Pilot: 100 live requests, all parsed (53 YES, 28 UNKNOWN, 19 NO).
- Batches submitted 14:54–14:55 AEDT; downloaded 15:53, 16:04, 16:37, 16:44 AEDT: 152,728 done, 0
  failed; **cost $1.39** (gpt-4o-mini Batch $0.075/$0.30 per million tokens, OpenAI's page 2026-10-24).
- Counts-only check before scoring: 100 % parsed, 81,629 stock-sessions, 81,628 mapped to a cache line.
- Frozen SHA-256: `exp028_build.py` `aaff4ad614d3b5c53c85f74bdc286cfb803a2af0663f7a5b81fe95ef8ca0f9f4`,
  `exp028_batch.py` `3763fe40dd431035ac6b0f095ec2431946ad3eefc0ef19ac6aaf26a9fbc42332`,
  `exp028_score.py` `4f0850281a567a43a3c3f8ebe4de637c027f2f08ad091be4b90f887594b1d123`; scored once
  05:45 UTC; `exp028.json` SHA-256 `000bfe55db4d551b949a78014a11a3e6fae4cbbfad0404ae313d1d1a35d6d9e3`.
  Kit OneDrive `trading-agents-data/exp028-2026-10-24/`.

```text
python exp028_build.py <news-alpaca> <OneDrive>/trading-agents-data <repo>/.env <kit>
python exp028_batch.py <kit> <repo>/.env
python exp028_score.py <kit> <OneDrive>/trading-agents-data <kit>/exp028.json
```

## Appendix S — Scripts

### `exp028_build.py`

```python
"""EXP-028 stage 1: the headline set and the OpenAI Batch request files. No price is read.

Headlines: Benzinga (Alpaca archive) created 2024-01-01 → 2026-09-24 (UTC), naming exactly one symbol
that is an S&P 500 member that day. Each is assigned the fleet's decision session (its nightly run at
18:30 ET). The prompt is Lopez-Lira and Tang's (2023).
Usage: python exp028_build.py <news_dir> <cache_dir> <env_file> <out_dir> [--pilot N]
"""

from __future__ import annotations

import gzip
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd
import tiktoken

MODELS = {"gpt-4o-mini-2024-07-18": ("o200k_base", 0.075, 0.30)}
START, END = "2024-01-01", "2026-09-24"
CHUNK = 40000
PROMPT = (
    "Forget all your previous instructions. Pretend you are a financial expert. You are a financial expert "
    "with stock recommendation experience. Answer \"YES\" if good news, \"NO\" if bad news, or \"UNKNOWN\" if "
    "uncertain in the first line. Then elaborate with one short and concise sentence on the next line. "
    "Is this headline good or bad for the stock price of {name} in the short term?\n\nHeadline: {headline}"
)


def norm(t: str) -> str:
    return str(t).upper().replace("-", ".").replace("/", ".")


def env(path: str) -> dict[str, str]:
    out = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def names(e: dict[str, str]) -> dict[str, str]:
    req = urllib.request.Request("https://paper-api.alpaca.markets/v2/assets?status=all&asset_class=us_equity",
                                 headers={"APCA-API-KEY-ID": e["ALPACA_PAPER_API_KEY"], "APCA-API-SECRET-KEY": e["ALPACA_API_SECRET"]})
    out = {}
    for a in json.load(urllib.request.urlopen(req, timeout=120)):
        sym = norm(a["symbol"])
        if a.get("name") and (sym not in out or a.get("status") == "active"):
            out[sym] = a["name"]
    return out


def main() -> None:
    news, cache, envf, out = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
    pilot = int(sys.argv[sys.argv.index("--pilot") + 1]) if "--pilot" in sys.argv else 0
    out.mkdir(parents=True, exist_ok=True)
    sessions = pd.DatetimeIndex(pd.read_csv(cache / "sp500_sessions.csv.gz")["date"])
    mem = pd.read_csv(cache / "sp500_membership.csv.gz")
    mem["key"] = mem["ticker"].map(norm)
    mem = mem[mem["last"] >= START]
    rows = []
    for f in sorted(news.glob("20*.jsonl.gz")):
        if f.name[:7] < START[:7] or f.name[:7] > END[:7]:
            continue
        for line in gzip.open(f, "rt", encoding="utf-8"):
            it = json.loads(line)
            syms = {norm(s) for s in it.get("symbols", [])}
            if len(syms) != 1 or not it.get("headline"):
                continue
            rows.append((str(it["id"]), syms.pop(), it["headline"].strip(), it["created_at"]))
    df = pd.DataFrame(rows, columns=["id", "symbol", "headline", "created_at"]).drop_duplicates("id")
    ts = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert("America/New_York")
    df["et_date"] = ts.dt.tz_localize(None).dt.normalize()
    df["et_minutes"] = ts.dt.hour * 60 + ts.dt.minute
    df = df[(ts.dt.tz_convert("UTC").dt.strftime("%Y-%m-%d") >= START) & (df["et_date"] <= END)]
    # the fleet's decision session: the run at 18:30 ET on a session day
    k = sessions.searchsorted(df["et_date"], side="left")
    k = pd.Series(k, index=df.index)
    on_session = sessions[k.clip(upper=len(sessions) - 1)] == df["et_date"].to_numpy()
    late = df["et_minutes"] > 18 * 60 + 30
    k = k + ((~on_session) * 0) + (on_session & late).astype(int)
    df["session"] = sessions[k.clip(upper=len(sessions) - 1)].to_numpy()
    df["tclass"] = "overnight"  # before the open of its decision session, or a non-session day
    same = df["et_date"] == df["session"]
    df.loc[same & (df["et_minutes"] >= 570) & (df["et_minutes"] < 960), "tclass"] = "market"
    df.loc[same & (df["et_minutes"] >= 960), "tclass"] = "after_close"
    df.loc[same & (df["et_minutes"] < 570), "tclass"] = "pre_open"
    # S&P 500 member on the headline's decision session
    ok = []
    by_key = {key: g for key, g in mem.groupby("key")}
    for sym, sess in zip(df["symbol"], df["session"].dt.strftime("%Y-%m-%d")):
        g = by_key.get(sym)
        ok.append(bool(g is not None and ((g["first"] <= sess) & (g["last"] >= sess)).any()))
    df = df[pd.Series(ok, index=df.index) & (df["session"] <= END)]
    df = df.assign(hkey=df["headline"].str.lower().str.strip()).drop_duplicates(["symbol", "session", "hkey"]).drop(columns="hkey")
    nm = names(env(envf))
    df["name"] = df["symbol"].map(lambda s: nm.get(s, s))
    if pilot:
        df = df.sample(n=pilot, random_state=0)
    df.sort_values(["session", "symbol", "id"]).to_csv(out / ("pilot_headlines.csv.gz" if pilot else "headlines.csv.gz"), index=False, compression="gzip")
    print("headlines", len(df), "symbols", df["symbol"].nunique(), "named", int((df["name"] != df["symbol"]).sum()),
          "sessions", df["session"].nunique(), "by class", df["tclass"].value_counts().to_dict())
    total = 0.0
    for model, (enc, pin, pout) in MODELS.items():
        tok = tiktoken.get_encoding(enc)
        n_in, files = 0, []
        lines = []
        for r in df.itertuples():
            content = PROMPT.format(name=r.name, headline=r.headline)
            n_in += len(tok.encode(content)) + 8
            lines.append(json.dumps({"custom_id": f"{r.id}|{r.symbol}", "method": "POST", "url": "/v1/chat/completions",
                                     "body": {"model": model, "messages": [{"role": "user", "content": content}],
                                              "max_tokens": 2, "temperature": 0}}))
        if not pilot:
            for i in range(0, len(lines), CHUNK):
                p = out / f"req_{model}_{i // CHUNK:02d}.jsonl"
                p.write_text("\n".join(lines[i : i + CHUNK]) + "\n", encoding="utf-8")
                files.append(p.name)
        cost = n_in / 1e6 * pin + len(lines) * 2 / 1e6 * pout
        total += cost
        print(model, "requests", len(lines), "input tokens", n_in, f"batch cost estimate ${cost:.2f}", files)
    print(f"total estimate ${total:.2f}")
    if total > 18:
        raise SystemExit("estimate above $18: refuse")


if __name__ == "__main__":
    main()
```

### `exp028_batch.py`

```python
"""EXP-028 stage 2: submit the request files to OpenAI's Batch API, wait, download the outputs.

Tries every file at once; a batch refused for the queue's token limit is resubmitted when the others
finish. Writes batches.json (ids, status, usage) and out_<file>.jsonl. Reads no price.
Usage: python exp028_batch.py <kit_dir> <env_file>
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from openai import OpenAI

PRICE_IN, PRICE_OUT = 0.075, 0.30  # gpt-4o-mini Batch, per 1M tokens (OpenAI pricing page, 2026-10-24)
CAP = 20.0


def env(path: str) -> dict[str, str]:
    out = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> None:
    kit = Path(sys.argv[1])
    client = OpenAI(api_key=env(sys.argv[2])["OPENAI_API_KEY"])
    state_path = kit / "batches.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    files = sorted(p.name for p in kit.glob("req_*.jsonl"))

    def submit(name):
        up = client.files.create(file=open(kit / name, "rb"), purpose="batch")
        b = client.batches.create(input_file_id=up.id, endpoint="/v1/chat/completions", completion_window="24h")
        state[name] = {"batch": b.id, "status": b.status}
        print(time.strftime("%H:%M:%S"), "submitted", name, b.id, flush=True)

    for name in files:
        if name not in state:
            submit(name)
    state_path.write_text(json.dumps(state, indent=1))
    while True:
        pending = False
        for name in files:
            s = state[name]
            if s["status"] in ("completed", "downloaded"):
                continue
            b = client.batches.retrieve(s["batch"])
            s["status"] = b.status
            s["counts"] = {"done": b.request_counts.completed, "failed": b.request_counts.failed, "total": b.request_counts.total}
            if b.status == "completed":
                text = client.files.content(b.output_file_id).text
                (kit / f"out_{name}").write_text(text, encoding="utf-8")
                tin = tout = 0
                for line in text.splitlines():
                    u = (json.loads(line).get("response") or {}).get("body", {}).get("usage") or {}
                    tin += u.get("prompt_tokens", 0)
                    tout += u.get("completion_tokens", 0)
                s["usage"] = {"in": tin, "out": tout, "cost": tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT}
                s["status"] = "downloaded"
                print(time.strftime("%H:%M:%S"), "downloaded", name, s["counts"], s["usage"], flush=True)
            elif b.status in ("failed", "expired", "cancelled"):
                errs = [e.code for e in (b.errors.data if b.errors else [])]
                print(time.strftime("%H:%M:%S"), name, b.status, errs, flush=True)
                if any("token_limit" in (c or "") for c in errs):
                    del state[name]  # resubmitted once a slot frees
                else:
                    raise SystemExit(f"{name} {b.status} {errs}")
            if s.get("status") not in ("downloaded",):
                pending = True
        for name in files:
            if name not in state:
                running = [n for n in files if n in state and state[n]["status"] not in ("downloaded",)]
                if not running:
                    submit(name)
                pending = True
        state_path.write_text(json.dumps(state, indent=1))
        spent = sum(s.get("usage", {}).get("cost", 0) for s in state.values())
        if spent > CAP:
            raise SystemExit(f"spent ${spent:.2f} above the cap")
        if not pending:
            print("all downloaded; cost", round(spent, 4), flush=True)
            return
        time.sleep(60)


if __name__ == "__main__":
    main()
```

### `exp028_score.py`

```python
"""EXP-028 stage 3: join the model's labels to next-day returns and apply the pre-registered bar.

Usage: python exp028_score.py <kit_dir> <sp500_cache_dir> <out.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

B, SEED, BLOCK = 5000, 0, 20


def norm(t: str) -> str:
    return str(t).upper().replace("-", ".").replace("/", ".")


def label(text: str) -> tuple[int, bool]:
    t = (text or "").strip().upper()
    if t.startswith("YES"):
        return 1, True
    if t.startswith("NO") and not t.startswith("NOT"):
        return -1, True
    return 0, t.startswith("UNK")


def labels(kit: Path) -> tuple[pd.DataFrame, dict]:
    rows, failed, total = [], 0, 0
    for f in sorted(kit.glob("out_req_*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            total += 1
            resp = r.get("response") or {}
            if r.get("error") or resp.get("status_code") != 200:
                failed += 1
                continue
            text = resp["body"]["choices"][0]["message"]["content"]
            lab, parsed = label(text)
            hid, sym = r["custom_id"].split("|", 1)
            rows.append((hid, sym, lab, parsed))
    df = pd.DataFrame(rows, columns=["id", "symbol", "label", "parsed"])
    return df, {"responses": total, "failed": failed, "parsed_share": float(df["parsed"].mean()),
                "yes": int((df["label"] == 1).sum()), "no": int((df["label"] == -1).sum()), "other": int((df["label"] == 0).sum())}


def stationary(n, rng):
    out = np.empty((B, n), np.int64)
    pos = np.arange(n)
    for k in range(B):
        st = rng.random(n) < 1.0 / BLOCK
        st[0] = True
        grp = np.cumsum(st) - 1
        first = pos[st]
        base = rng.integers(n, size=len(first))
        out[k] = (base[grp] + pos - first[grp]) % n
    return out


def main() -> None:
    kit, cache, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    lab, lab_stats = labels(kit)
    h = pd.read_csv(kit / "headlines.csv.gz", dtype={"id": str}, parse_dates=["session"])
    h = h.merge(lab, on=["id", "symbol"], how="inner")
    bars = pd.read_csv(cache / "sp500_bars.csv.gz", parse_dates=["date"])
    bars = bars[bars["date"] >= "2023-12-01"]
    bars["key"] = bars["symbol"].map(norm)
    O = bars.pivot(index="date", columns="line", values="open").sort_index()
    C = bars.pivot(index="date", columns="line", values="close").reindex(O.index)
    cal = O.index
    mem = pd.read_csv(cache / "sp500_membership.csv.gz", parse_dates=["first", "last"])
    member = pd.DataFrame(False, index=cal, columns=O.columns)
    for r in mem.itertuples():
        if r.line in member.columns:
            member.loc[(cal >= r.first) & (cal <= r.last), r.line] = True
    key_line = bars.drop_duplicates(["key", "date"]).set_index(["key", "date"])["line"]
    Ov, Cv, Mv = O.to_numpy(), C.to_numpy(), member.to_numpy()
    nxt = lambda a: np.vstack([a[1:], np.full((1, a.shape[1]), np.nan)])  # noqa: E731
    prv = lambda a: np.vstack([np.full((1, a.shape[1]), np.nan), a[:-1]])  # noqa: E731
    win = {"DAY": nxt(Cv) / nxt(Ov) - 1, "OVN": nxt(Ov) / Cv - 1, "CC": nxt(Cv) / Cv - 1, "DAY0": Cv / Ov - 1}
    excess = {}
    for k, w in win.items():
        w = np.where(Mv, w, np.nan)
        excess[k] = w - np.nanmean(w, axis=1, keepdims=True)
    pos = {d: i for i, d in enumerate(cal)}
    lines = {l: j for j, l in enumerate(O.columns)}

    def signals(frame: pd.DataFrame) -> pd.DataFrame:
        g = frame.groupby(["symbol", "session"])["label"].mean().reset_index()
        g["i"] = g["session"].map(pos)
        g["line"] = [key_line.get((s, d)) for s, d in zip(g["symbol"], g["session"])]
        g = g.dropna(subset=["i", "line"])
        g["j"] = g["line"].map(lines)
        g = g.dropna(subset=["j"])
        g["i"], g["j"] = g["i"].astype(int), g["j"].astype(int)
        for k in excess:
            g[k] = excess[k][g["i"].to_numpy(), g["j"].to_numpy()]
        return g

    rng = np.random.default_rng(SEED)
    sig = signals(h)
    good = sig[sig["label"] > 0].dropna(subset=["DAY"])
    p = good.groupby("i")["DAY"].mean().sort_index()
    res = {"labels": lab_stats, "headlines_scored": int(len(h)), "stock_sessions": int(len(sig)),
           "good_stock_sessions": int((sig["label"] > 0).sum()), "bad_stock_sessions": int((sig["label"] < 0).sum())}
    draws = stationary(len(p), rng)
    for cost, tag in ((0.0005, "5bps"), (0.0010, "10bps"), (0.0025, "25bps")):
        net = p.to_numpy() - 2 * cost
        boot = net[draws].mean(1)
        half = len(net) // 2
        res[f"primary_{tag}"] = {"sessions": int(len(net)), "mean_net_pct": float(net.mean() * 100),
                                 "ci95_pct": [float(np.percentile(boot, 2.5) * 100), float(np.percentile(boot, 97.5) * 100)],
                                 "halves_pct": [float(net[:half].mean() * 100), float(net[half:].mean() * 100)],
                                 "hit_rate": float((net > 0).mean())}
    pr = res["primary_5bps"]
    res["verdict"] = "EDGE" if (pr["ci95_pct"][0] > 0 and min(pr["halves_pct"]) > 0) else "NONE"
    res["primary_gross_mean_pct"] = float(p.mean() * 100)

    def spread(frame, k):
        f = frame.dropna(subset=[k])
        gm = f[f["label"] > 0].groupby("i")[k].mean()
        bm = f[f["label"] < 0].groupby("i")[k].mean()
        both = gm.index.intersection(bm.index)
        d = (gm[both] - bm[both]).sort_index().to_numpy()
        if len(d) < 30:
            return {"sessions": int(len(d))}
        dr = stationary(len(d), rng)[:1000]
        bt = d[dr].mean(1)
        return {"sessions": int(len(d)), "good_pct": float(gm.mean() * 100), "bad_pct": float(bm.mean() * 100),
                "spread_pct": float(d.mean() * 100), "spread_ci95_pct": [float(np.percentile(bt, 2.5) * 100), float(np.percentile(bt, 97.5) * 100)]}

    sec = {}
    for k in ("DAY", "OVN", "CC"):
        sec[f"all_{k}"] = spread(sig, k)
    for cls in ("market", "after_close", "pre_open", "overnight"):
        s = signals(h[h["tclass"] == cls])
        sec[f"{cls}"] = {k: spread(s, k) for k in ("DAY", "OVN", "CC")}
        if cls in ("pre_open", "overnight"):
            sec[f"{cls}"]["DAY0"] = spread(s, "DAY0")
    early = signals(h[h["tclass"].isin(["pre_open", "overnight"])])
    sec["early_read_buy_at_open_DAY0"] = spread(early, "DAY0")
    years = {}
    for y in (2024, 2025, 2026):
        m = cal[p.index].year == y
        years[str(y)] = {"sessions": int(m.sum()), "gross_pct": float(p[m].mean() * 100), "net5_pct": float((p[m] - 0.001).mean() * 100)}
    res["by_year"] = years
    res["secondary"] = sec
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("labels", "verdict", "primary_gross_mean_pct", "primary_5bps", "primary_25bps")}, indent=1))


if __name__ == "__main__":
    main()
```
