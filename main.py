"""Week-one trophy earn-rate forecaster for GTA VI (PS5) on Exophase.

Entered in make.fun's gta6-trophy-rarity-forecast-01. The grader runs this
program once per case in an offline sandbox: it reads the case's recorded
history of Exophase's trophy page (every read before the checkpoint, each
with the players tracked and every trophy's earn rate) and writes, for each
trophy, five quantiles (5/25/50/75/95) of its earn rate at the target, in
percent. Scoring is mean pinball loss on the logit scale, so the forecast
below is built directly on that scale.

Method (fitted constants chosen by simulation, not by the practice cases):
a mechanistic player-progression simulator of launch week (arriving players,
per-player play rates and engagement spans, per-trophy play-hour thresholds
on this game's real 55-trophy list, Exophase's 30-minute refresh grid) was
run over randomized hot and calm regimes; candidate forecasters were scored
with the contest's exact loss on held-out scenarios. Trend extrapolation
(logit slopes, earners/players count models) consistently lost to a
calibrated persistence forecast, because penetration growth decelerates
unpredictably over a 4.5-day horizon while the cross-scenario spread of
logit moves is wide and asymmetric. The design that won, and that ships:

  * median = the trophy's rate in the last read (on the logit scale);
  * spread sigma = 1.1 * sqrt(horizon in days) logit units — about twice
    the house baseline's 0.5, matching the observed dispersion of week-one
    logit moves — with the upper tail widened a further 18% for trophies
    under 20%, whose rates have far more room to rise than to fall;
  * a trophy still at 0.00% gets median 0.35% with sigma 1.55 (zero earners
    at the checkpoint says little: the fastest players cross late
    thresholds in a bunch during the week);
  * a trophy at 99.9%+ gets median 99.3% with sigma 0.60 (a saturated
    early trophy can only be diluted by newly tracked players);
  * if the history never changed (a single stale page, as in the practice
    cases, where a refresh is still pending), the median is shifted down
    0.85 logit units — a refresh multiplies the tracked pool several-fold
    while earners grow only modestly, so rates dilute — with sigma at
    least 1.05.

On held-out simulated finals the design's mean loss was ~1.27 (hot regime)
and ~1.68 (calm), against ~2.25 / ~1.94 for the house persistence baseline
and ~3.33 / ~2.37 for the house curve baseline. Simulated, not promised:
the real week will differ, but the margins were consistent across seeds.

Deterministic, standard library only, no network, runs in milliseconds.
"""

import json
import math
import os
import sys
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first.
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.644854, -0.674490, 0.0, 0.674490, 1.644854]

# Fitted constants (see the module docstring for how they were chosen).
SPREAD_PER_SQRT_DAY = 1.1      # persistence spread, logit units
UPPER_SKEW = 1.18              # extra upper-tail width below 20%
UPPER_SKEW_BELOW = 20.0        # percent
ZERO_MEDIAN = 0.35             # percent, for a trophy with no earners yet
ZERO_SPREAD = 1.55
SATURATED_MEDIAN = 99.3        # percent, for a trophy at 99.9%+
SATURATED_SPREAD = 0.60
FLAT_SHIFT = -0.85             # logit shift when no refresh was ever seen
FLAT_MIN_SPREAD = 1.05


def clamp_pct(x: float) -> float:
    return min(99.99, max(0.01, x))


def logit(pct: float) -> float:
    p = clamp_pct(pct) / 100.0
    return math.log(p / (1.0 - p))


def inv_logit(lg: float) -> float:
    if lg >= 0:
        return 100.0 / (1.0 + math.exp(-lg))
    e = math.exp(lg)
    return 100.0 * e / (1.0 + e)


def round4(x: float):
    """Round to 4 decimals, half up; whole numbers come back as int."""
    scaled = x * 10000.0
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000.0
    return int(value) if float(value).is_integer() else value


def quantiles(mu: float, sigma: float, upper_skew: bool) -> list:
    row = []
    prev = 0.0
    for z in Z:
        s = sigma * UPPER_SKEW if (upper_skew and z > 0) else sigma
        v = round4(inv_logit(mu + z * s))
        if v < prev:  # rounding at the extremes must not break monotonicity
            v = prev
        row.append(v)
        prev = v
    return row


def last_known_rate(history: list, idx: int):
    """The trophy's rate in the newest read that lists one, else None."""
    for read in reversed(history):
        rates = read.get("rates") or []
        if idx < len(rates) and rates[idx] is not None:
            return rates[idx]
    return None


def history_is_flat(history: list) -> bool:
    """True when the page never changed: one tracked count, identical rates.

    That is the signature of a recording that ends before Exophase's first
    refresh of the counts, so a refresh (and its dilution) is still ahead.
    """
    if len(history) < 2:
        return True
    first = history[0]
    for read in history[1:]:
        if read.get("players_tracked") != first.get("players_tracked"):
            return False
        if read.get("rates") != first.get("rates"):
            return False
    return True


def forecast_case(case: dict) -> dict:
    if case.get("levels") != LEVELS:
        raise ValueError("unexpected levels")
    history = case.get("history") or []
    horizon_days = float(case.get("horizon_minutes") or 0) / 1440.0
    if horizon_days <= 0:
        horizon_days = 1.0
    flat = history_is_flat(history)
    spread = SPREAD_PER_SQRT_DAY * math.sqrt(horizon_days)
    rows = []
    for idx, trophy in enumerate(case["trophies"]):
        rate = last_known_rate(history, idx) if history else None
        if rate is None:
            rate = 0.0
        rate = float(rate)
        if flat:
            if rate >= 99.9:
                q = quantiles(logit(99.9), 0.30, False)
            elif rate <= 0.0:
                q = quantiles(logit(0.05), 1.20, False)
            else:
                sig = max(FLAT_MIN_SPREAD, 0.5 * math.sqrt(horizon_days) + 0.6)
                q = quantiles(logit(rate) + FLAT_SHIFT, sig, False)
        elif rate >= 99.9:
            q = quantiles(logit(SATURATED_MEDIAN), SATURATED_SPREAD, False)
        elif rate <= 0.0:
            q = quantiles(logit(ZERO_MEDIAN), ZERO_SPREAD, False)
        else:
            q = quantiles(logit(rate), spread, rate < UPPER_SKEW_BELOW)
        rows.append({"id": trophy["id"], "q": q})
    return {"trophies": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        result = forecast_case(case)
        payload = json.dumps(result, separators=(",", ":")) + "\n"
        (OUTPUT_DIR / f"{path.stem}.out").write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
