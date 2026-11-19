# gta6-trophy-rarity-forecast-01

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/Iceland26/gta6-trophy-rarity-forecast-01/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/Iceland26/gta6-trophy-rarity-forecast-01/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

A forecaster for Grand Theft Auto VI's PS5 trophy earn rates on Exophase at
the end of launch week. The grader feeds the program one case at a time —
the recorded history of the game's Exophase trophy page before a checkpoint
— and the program writes five quantiles (5/25/50/75/95) of every trophy's
earn rate at the target. Scoring is mean pinball loss on the logit scale.

The method is a calibrated persistence forecast on the logit scale, with
three corrections that simulation over randomized launch-week regimes
(player arrivals, play rates, engagement spans, per-trophy play-hour
thresholds on the game's real 55-trophy list, Exophase's refresh grid)
showed to matter: a spread of 1.1·√(horizon days) logit units, an 18%
wider upper tail for trophies under 20%, a 0.35% median with a wide spread
for trophies nobody has earned yet, a dilution-aware treatment of
saturated trophies, and a downward median shift when the recorded page
never refreshed. Trend-extrapolation and earners/players count models were
built and tested the same way and lost to this design on held-out
scenarios; the shipped program's docstring carries the numbers.

Python 3.13, standard library only, deterministic, offline, milliseconds
per case.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

(with a directory of `*.in` case files in place of `input/`)

---

<sub>Entered on [make.fun](https://make.fun) in the "Forecast how many GTA VI players earn each trophy in week one" bounty.</sub>
