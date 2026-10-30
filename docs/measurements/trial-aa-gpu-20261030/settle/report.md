# A/A rounds of paired trials: the null, the current rule, candidate rules

x = log(t_AA / t_preference) per round: an equal challenger's log ratio. Rates are per contest, for independent rounds drawn from the measured null round by round (a process's first three contest rounds each from its own sample, later rounds and confirmations by the order's parity: Null), unless a line says otherwise; m equal challengers are taken as independent (an upper bound). Powers are for one challenger of the stated gain, its noise the A/A arm's.

## Candidate rules against D8 (no looser than the current measured false-switch rate)

False-switch rates are per contest at gain 0 for each group's m equal challengers (Holm: alpha / m per arm; the current rule with its confirmation). "Every group": the test's rate is no larger than the current rule's under each group's null; "worst": its largest rate is no larger than the current rule's largest (0.15, dev3-before). "With the contest effect": the same two with each group's contest effect added to both rules (an upper bound for each; the current rule's largest is then 0.15). "Keeps power": its power at 5% and 10% is at least the current rule's under every group's null, exactly; where it is not, the largest shortfall and where. Listed: every rule that meets "every group", those that meet "worst" and keep the power, and the rules compared below (the per-group rates of all are below). Power for one challenger of the gain, worst group / best group; rounds: the largest expected count at gain 0 and at 5%, and the rounds a challenger that loses every round runs (the usual case: on most banks the CPU's challengers are 1.1-2.2x slower), which with each group's cost of a round (below) is the trial's overhead.

| rule | every group | worst | with the contest effect: every / worst | keeps power | power (worst / best) 2% | power (worst / best) 5% | power (worst / best) 10% | rounds at 0 / 5% | rounds, all lost |
|---|---|---|---|---|---|---|---|---|---|
| current (TIE 5%, 75%, 5/10, confirm) | (reference) | (reference) | (reference) | (reference) | 0.000 / 0.175 | 0.000 / 0.424 | 0.013 / 1.000 | 5.9 / 5.9 | 3 |
| sign, delta 0.015, alpha 0.05, cap 20 | no | yes | no / yes | yes | 0.001 / 0.836 | 0.001 / 1.000 | 0.419 / 1.000 | 12.0 / 12.8 | 5 |
| sign, delta 0.02, alpha 0.01, cap 20 | no | yes | no / yes | no: 0.23 short at 10% (dev3-before) | 0.000 / 0.223 | 0.000 / 0.987 | 0.180 / 1.000 | 10.4 / 12.8 | 4 |
| sign, delta 0.03, alpha 0.005, cap 10 | yes | yes | yes / yes | no: 0.55 short at 10% (dev3-after) | 0.000 / 0.006 | 0.000 / 0.561 | 0.008 / 1.000 | 2.5 / 6.3 | 1 |
| sign, delta 0.03, alpha 0.003, cap 10 | yes | yes | yes / yes | no: 0.58 short at 10% (dev3-after) | 0.000 / 0.004 | 0.000 / 0.522 | 0.005 / 1.000 | 2.5 / 6.9 | 1 |
| sign, delta 0.03, alpha 0.003, cap 20 | no | yes | no / yes | no: 0.29 short at 10% (dev3-before) | 0.000 / 0.021 | 0.000 / 0.960 | 0.007 / 1.000 | 10.5 / 14.9 | 4 |
| sign, delta 0.03, alpha 0.002, cap 10 | yes | yes | yes / yes | no: 0.58 short at 10% (dev3-after) | 0.000 / 0.004 | 0.000 / 0.522 | 0.005 / 1.000 | 2.5 / 6.9 | 1 |
| sign, delta 0.03, alpha 0.001, cap 10 | yes | yes | yes / yes | no: 0.61 short at 10% (dev3-after) | 0.000 / 0.002 | 0.000 / 0.486 | 0.004 / 1.000 | 2.5 / 7.4 | 1 |
| sign, delta 0.03, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.61 short at 10% (dev3-after) | 0.000 / 0.000 | 0.000 / 0.631 | 0.000 / 1.000 | 5.5 / 14.5 | 2 |
| sign, delta 0.03, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.38 short at 10% (dev3-after) | 0.000 / 0.002 | 0.000 / 0.952 | 0.000 / 1.000 | 13.1 / 22.6 | 5 |
| sign, delta 0.03, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.33 short at 10% (dev3-before) | 0.000 / 0.005 | 0.000 / 0.995 | 0.000 / 1.000 | 20.6 / 29.9 | 8 |
| sign, delta 0.04, alpha 0.02, cap 30 | yes | yes | yes / yes | no: 0.054 short at 5% (dev3-before) | 0.000 / 0.118 | 0.000 / 0.986 | 0.005 / 1.000 | 18.7 / 20.3 | 8 |
| sign, delta 0.04, alpha 0.02, cap 40 | yes | yes | yes / yes | no: 0.0083 short at 10% (dev2-before) | 0.000 / 0.159 | 0.000 / 0.999 | 0.005 / 1.000 | 27.5 / 28.9 | 12 |
| sign, delta 0.04, alpha 0.01, cap 20 | yes | yes | yes / yes | no: 0.25 short at 10% (dev3-before) | 0.000 / 0.038 | 0.000 / 0.844 | 0.004 / 1.000 | 9.9 / 12.0 | 4 |
| sign, delta 0.04, alpha 0.01, cap 30 | yes | yes | yes / yes | no: 0.12 short at 5% (dev3-before) | 0.000 / 0.077 | 0.000 / 0.980 | 0.002 / 1.000 | 19.1 / 21.2 | 8 |
| sign, delta 0.04, alpha 0.01, cap 40 | yes | yes | yes / yes | no: 0.056 short at 5% (dev3-before) | 0.000 / 0.101 | 0.000 / 0.996 | 0.001 / 1.000 | 25.9 / 28.2 | 11 |
| sign, delta 0.04, alpha 0.005, cap 10 | yes | yes | yes / yes | no: 0.55 short at 10% (dev3-after) | 0.000 / 0.004 | 0.000 / 0.341 | 0.003 / 1.000 | 2.1 / 5.3 | 1 |
| sign, delta 0.04, alpha 0.005, cap 20 | yes | yes | yes / yes | no: 0.3 short at 10% (dev3-before) | 0.000 / 0.021 | 0.000 / 0.802 | 0.001 / 1.000 | 10.0 / 13.4 | 4 |
| sign, delta 0.04, alpha 0.005, cap 30 | yes | yes | yes / yes | no: 0.18 short at 5% (dev3-before) | 0.000 / 0.043 | 0.000 / 0.955 | 0.001 / 1.000 | 16.9 / 19.6 | 7 |
| sign, delta 0.04, alpha 0.005, cap 40 | yes | yes | yes / yes | no: 0.12 short at 5% (dev3-before) | 0.000 / 0.064 | 0.000 / 0.994 | 0.000 / 1.000 | 26.2 / 29.2 | 11 |
| sign, delta 0.04, alpha 0.003, cap 10 | yes | yes | yes / yes | no: 0.58 short at 10% (dev3-after) | 0.000 / 0.002 | 0.000 / 0.299 | 0.001 / 1.000 | 2.1 / 5.7 | 1 |
| sign, delta 0.04, alpha 0.003, cap 20 | yes | yes | yes / yes | no: 0.31 short at 10% (dev3-before) | 0.000 / 0.017 | 0.000 / 0.787 | 0.000 / 1.000 | 10.0 / 14.5 | 4 |
| sign, delta 0.04, alpha 0.003, cap 30 | yes | yes | yes / yes | no: 0.23 short at 10% (dev3-before) | 0.000 / 0.028 | 0.000 / 0.941 | 0.000 / 1.000 | 17.0 / 20.1 | 7 |
| sign, delta 0.04, alpha 0.003, cap 40 | yes | yes | yes / yes | no: 0.17 short at 5% (dev3-before) | 0.000 / 0.043 | 0.000 / 0.987 | 0.000 / 1.000 | 24.0 / 27.8 | 10 |
| sign, delta 0.04, alpha 0.002, cap 10 | yes | yes | yes / yes | no: 0.58 short at 10% (dev3-after) | 0.000 / 0.002 | 0.000 / 0.299 | 0.001 / 1.000 | 2.1 / 5.7 | 1 |
| sign, delta 0.04, alpha 0.002, cap 20 | yes | yes | yes / yes | no: 0.37 short at 10% (dev3-after) | 0.000 / 0.007 | 0.000 / 0.640 | 0.000 / 1.000 | 7.6 / 12.9 | 3 |
| sign, delta 0.04, alpha 0.002, cap 30 | yes | yes | yes / yes | no: 0.25 short at 10% (dev3-before) | 0.000 / 0.023 | 0.000 / 0.936 | 0.000 / 1.000 | 17.0 / 20.4 | 7 |
| sign, delta 0.04, alpha 0.002, cap 40 | yes | yes | yes / yes | no: 0.2 short at 5% (dev3-before) | 0.000 / 0.030 | 0.000 / 0.983 | 0.000 / 1.000 | 24.1 / 28.4 | 10 |
| sign, delta 0.04, alpha 0.001, cap 10 | yes | yes | yes / yes | no: 0.61 short at 10% (dev3-after) | 0.000 / 0.001 | 0.000 / 0.261 | 0.000 / 1.000 | 2.1 / 6.0 | 1 |
| sign, delta 0.04, alpha 0.001, cap 20 | yes | yes | yes / yes | no: 0.43 short at 10% (dev3-after) | 0.000 / 0.004 | 0.000 / 0.588 | 0.000 / 1.000 | 7.6 / 14.5 | 3 |
| sign, delta 0.04, alpha 0.001, cap 30 | yes | yes | yes / yes | no: 0.31 short at 10% (dev3-before) | 0.000 / 0.011 | 0.000 / 0.873 | 0.000 / 1.000 | 14.7 / 19.6 | 6 |
| sign, delta 0.04, alpha 0.001, cap 40 | yes | yes | yes / yes | no: 0.24 short at 10% (dev3-before) | 0.000 / 0.018 | 0.000 / 0.966 | 0.000 / 1.000 | 21.8 / 26.4 | 9 |
| sign, delta 0.04, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.61 short at 10% (dev3-after) | 0.000 / 0.000 | 0.000 / 0.312 | 0.000 / 1.000 | 5.2 / 12.3 | 2 |
| sign, delta 0.04, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.38 short at 10% (dev3-after) | 0.000 / 0.002 | 0.000 / 0.703 | 0.000 / 1.000 | 12.4 / 22.8 | 5 |
| sign, delta 0.04, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.35 short at 10% (dev3-before) | 0.000 / 0.003 | 0.000 / 0.896 | 0.000 / 1.000 | 19.5 / 27.6 | 8 |
| sign, delta 0.05, alpha 0.02, cap 30 | yes | yes | yes / yes | no: 0.054 short at 5% (dev3-before) | 0.000 / 0.098 | 0.000 / 0.464 | 0.002 / 1.000 | 18.7 / 20.3 | 8 |
| sign, delta 0.05, alpha 0.02, cap 40 | yes | yes | yes / yes | no: 0.011 short at 10% (dev2-before) | 0.000 / 0.129 | 0.000 / 0.599 | 0.002 / 1.000 | 27.5 / 28.9 | 12 |
| sign, delta 0.05, alpha 0.01, cap 20 | yes | yes | yes / yes | no: 0.25 short at 10% (dev3-before) | 0.000 / 0.031 | 0.000 / 0.223 | 0.002 / 1.000 | 9.9 / 11.7 | 4 |
| sign, delta 0.05, alpha 0.01, cap 30 | yes | yes | yes / yes | no: 0.12 short at 5% (dev3-before) | 0.000 / 0.062 | 0.000 / 0.383 | 0.001 / 1.000 | 19.1 / 21.2 | 8 |
| sign, delta 0.05, alpha 0.01, cap 40 | yes | yes | yes / yes | no: 0.07 short at 5% (dev3-after) | 0.000 / 0.079 | 0.000 / 0.490 | 0.001 / 1.000 | 25.9 / 28.2 | 11 |
| sign, delta 0.05, alpha 0.005, cap 10 | yes | yes | yes / yes | no: 0.58 short at 10% (dev3-after) | 0.000 / 0.001 | 0.000 / 0.062 | 0.002 / 1.000 | 2.0 / 3.5 | 1 |
| sign, delta 0.05, alpha 0.005, cap 20 | yes | yes | yes / yes | no: 0.3 short at 10% (dev3-before) | 0.000 / 0.017 | 0.000 / 0.165 | 0.001 / 1.000 | 10.0 / 12.2 | 4 |
| sign, delta 0.05, alpha 0.005, cap 30 | yes | yes | yes / yes | no: 0.18 short at 5% (dev3-before) | 0.000 / 0.034 | 0.000 / 0.281 | 0.000 / 1.000 | 16.9 / 20.2 | 7 |
| sign, delta 0.05, alpha 0.005, cap 40 | yes | yes | yes / yes | no: 0.12 short at 5% (dev3-before) | 0.000 / 0.049 | 0.000 / 0.406 | 0.000 / 1.000 | 26.2 / 29.2 | 11 |
| sign, delta 0.05, alpha 0.003, cap 10 | yes | yes | yes / yes | no: 0.61 short at 10% (dev3-after) | 0.000 / 0.000 | 0.000 / 0.044 | 0.000 / 1.000 | 2.0 / 3.5 | 1 |
| sign, delta 0.05, alpha 0.003, cap 20 | yes | yes | yes / yes | no: 0.31 short at 10% (dev3-before) | 0.000 / 0.013 | 0.000 / 0.143 | 0.000 / 1.000 | 10.0 / 12.5 | 4 |
| sign, delta 0.05, alpha 0.003, cap 30 | yes | yes | yes / yes | no: 0.23 short at 10% (dev3-before) | 0.000 / 0.021 | 0.000 / 0.224 | 0.000 / 1.000 | 17.0 / 20.9 | 7 |
| sign, delta 0.05, alpha 0.003, cap 40 | yes | yes | yes / yes | no: 0.17 short at 5% (dev3-before) | 0.000 / 0.033 | 0.000 / 0.329 | 0.000 / 1.000 | 24.0 / 28.2 | 10 |
| sign, delta 0.05, alpha 0.002, cap 10 | yes | yes | yes / yes | no: 0.61 short at 10% (dev3-after) | 0.000 / 0.000 | 0.000 / 0.044 | 0.000 / 1.000 | 2.0 / 3.5 | 1 |
| sign, delta 0.05, alpha 0.002, cap 20 | yes | yes | yes / yes | no: 0.42 short at 10% (dev3-after) | 0.000 / 0.006 | 0.000 / 0.090 | 0.000 / 1.000 | 7.6 / 9.7 | 3 |
| sign, delta 0.05, alpha 0.002, cap 30 | yes | yes | yes / yes | no: 0.25 short at 10% (dev3-before) | 0.000 / 0.017 | 0.000 / 0.207 | 0.000 / 1.000 | 17.0 / 21.2 | 7 |
| sign, delta 0.05, alpha 0.002, cap 40 | yes | yes | yes / yes | no: 0.2 short at 5% (dev3-before) | 0.000 / 0.022 | 0.000 / 0.276 | 0.000 / 1.000 | 24.1 / 29.1 | 10 |
| sign, delta 0.05, alpha 0.001, cap 10 | yes | yes | yes / yes | no: 0.63 short at 10% (dev3-after) | 0.000 / 0.000 | 0.000 / 0.031 | 0.000 / 1.000 | 2.0 / 3.5 | 1 |
| sign, delta 0.05, alpha 0.001, cap 20 | yes | yes | yes / yes | no: 0.48 short at 10% (dev3-after) | 0.000 / 0.003 | 0.000 / 0.060 | 0.000 / 1.000 | 7.6 / 9.9 | 3 |
| sign, delta 0.05, alpha 0.001, cap 30 | yes | yes | yes / yes | no: 0.31 short at 10% (dev3-before) | 0.000 / 0.008 | 0.000 / 0.134 | 0.000 / 1.000 | 14.7 / 18.9 | 6 |
| sign, delta 0.05, alpha 0.001, cap 40 | yes | yes | yes / yes | no: 0.24 short at 10% (dev3-before) | 0.000 / 0.013 | 0.000 / 0.207 | 0.000 / 1.000 | 21.8 / 27.4 | 9 |
| sign, delta 0.05, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.64 short at 10% (dev3-after) | 0.000 / 0.000 | 0.000 / 0.015 | 0.000 / 1.000 | 5.2 / 6.8 | 2 |
| sign, delta 0.05, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.45 short at 10% (dev3-after) | 0.000 / 0.001 | 0.000 / 0.044 | 0.000 / 1.000 | 12.4 / 16.6 | 5 |
| sign, delta 0.05, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.35 short at 10% (dev3-before) | 0.000 / 0.002 | 0.000 / 0.082 | 0.000 / 1.000 | 19.5 / 26.1 | 8 |

The cost of a round, per group: the mean over its rounds of every run but the preference's timed one (each configuration is settled and timed: twice its time; the A/A arm, a diagnostic, left out): dev2-before 0.00404 s; dev2-after 0.00353 s; dev3-before 0.0327 s; dev3-after 0.0303 s; dev4-before 0.0405 s; dev4-after 0.0401 s.

Per group, for every candidate that exists at alpha / m within its cap (false-switch rate, the current rule's, and both with the group's contest effect added):

| rule | dev2-before | dev2-after | dev3-before | dev3-after | dev4-before | dev4-after |
|---|---|---|---|---|---|---|
| delta 0, alpha 0.05, cap 10 | 0.0096 vs 3.5e-06 (0.0096 vs 3.5e-06) | 0.27 vs 3.2e-09 (0.27 vs 3.2e-09) | 0.076 vs 0.15 (0.076 vs 0.15) | 0.087 vs 0.0045 (0.087 vs 0.0045) | 0.14 vs 7.4e-10 (0.14 vs 7.4e-10) | 0.012 vs <1e-12 (0.012 vs <1e-12) |
| delta 0, alpha 0.05, cap 20 | 0.0012 vs 3.5e-06 (0.0012 vs 3.5e-06) | 0.45 vs 3.2e-09 (0.45 vs 3.2e-09) | 0.24 vs 0.15 (0.24 vs 0.15) | 0.17 vs 0.0045 (0.17 vs 0.0045) | 0.24 vs 7.4e-10 (0.24 vs 7.4e-10) | 0.0088 vs <1e-12 (0.0088 vs <1e-12) |
| delta 0, alpha 0.05, cap 30 | 0.0012 vs 3.5e-06 (0.0012 vs 3.5e-06) | 0.62 vs 3.2e-09 (0.62 vs 3.2e-09) | 0.37 vs 0.15 (0.37 vs 0.15) | 0.25 vs 0.0045 (0.25 vs 0.0045) | 0.34 vs 7.4e-10 (0.34 vs 7.4e-10) | 0.0076 vs <1e-12 (0.0076 vs <1e-12) |
| delta 0, alpha 0.05, cap 40 | 0.00016 vs 3.5e-06 (0.00016 vs 3.5e-06) | 0.74 vs 3.2e-09 (0.74 vs 3.2e-09) | 0.49 vs 0.15 (0.49 vs 0.15) | 0.31 vs 0.0045 (0.31 vs 0.0045) | 0.43 vs 7.4e-10 (0.43 vs 7.4e-10) | 0.0052 vs <1e-12 (0.0052 vs <1e-12) |
| delta 0, alpha 0.02, cap 10 | 0.00016 vs 3.5e-06 (0.00016 vs 3.5e-06) | 0.18 vs 3.2e-09 (0.18 vs 3.2e-09) | 0.049 vs 0.15 (0.049 vs 0.15) | 0.048 vs 0.0045 (0.048 vs 0.0045) | 0.078 vs 7.4e-10 (0.078 vs 7.4e-10) | 0.0027 vs <1e-12 (0.0027 vs <1e-12) |
| delta 0, alpha 0.02, cap 20 | 0.00015 vs 3.5e-06 (0.00015 vs 3.5e-06) | 0.33 vs 3.2e-09 (0.33 vs 3.2e-09) | 0.14 vs 0.15 (0.14 vs 0.15) | 0.094 vs 0.0045 (0.094 vs 0.0045) | 0.14 vs 7.4e-10 (0.14 vs 7.4e-10) | 0.0027 vs <1e-12 (0.0027 vs <1e-12) |
| delta 0, alpha 0.02, cap 30 | 2e-05 vs 3.5e-06 (2e-05 vs 3.5e-06) | 0.46 vs 3.2e-09 (0.46 vs 3.2e-09) | 0.23 vs 0.15 (0.23 vs 0.15) | 0.14 vs 0.0045 (0.14 vs 0.0045) | 0.21 vs 7.4e-10 (0.21 vs 7.4e-10) | 0.002 vs <1e-12 (0.002 vs <1e-12) |
| delta 0, alpha 0.02, cap 40 | 2e-05 vs 3.5e-06 (2e-05 vs 3.5e-06) | 0.6 vs 3.2e-09 (0.6 vs 3.2e-09) | 0.32 vs 0.15 (0.32 vs 0.15) | 0.19 vs 0.0045 (0.19 vs 0.0045) | 0.28 vs 7.4e-10 (0.28 vs 7.4e-10) | 0.0017 vs <1e-12 (0.0017 vs <1e-12) |
| delta 0, alpha 0.01, cap 10 | 0.00015 vs 3.5e-06 (0.00015 vs 3.5e-06) | 0.089 vs 3.2e-09 (0.089 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.017 vs 0.0045 (0.017 vs 0.0045) | 0.034 vs 7.4e-10 (0.034 vs 7.4e-10) | 0.0016 vs <1e-12 (0.0016 vs <1e-12) |
| delta 0, alpha 0.01, cap 20 | 1.9e-05 vs 3.5e-06 (1.9e-05 vs 3.5e-06) | 0.22 vs 3.2e-09 (0.22 vs 3.2e-09) | 0.077 vs 0.15 (0.077 vs 0.15) | 0.053 vs 0.0045 (0.053 vs 0.0045) | 0.087 vs 7.4e-10 (0.087 vs 7.4e-10) | 0.0011 vs <1e-12 (0.0011 vs <1e-12) |
| delta 0, alpha 0.01, cap 30 | 2.5e-06 vs 3.5e-06 (2.5e-06 vs 3.5e-06) | 0.38 vs 3.2e-09 (0.38 vs 3.2e-09) | 0.17 vs 0.15 (0.17 vs 0.15) | 0.095 vs 0.0045 (0.095 vs 0.0045) | 0.15 vs 7.4e-10 (0.15 vs 7.4e-10) | 0.00076 vs <1e-12 (0.00076 vs <1e-12) |
| delta 0, alpha 0.01, cap 40 | 2.4e-06 vs 3.5e-06 (2.4e-06 vs 3.5e-06) | 0.49 vs 3.2e-09 (0.49 vs 3.2e-09) | 0.23 vs 0.15 (0.23 vs 0.15) | 0.12 vs 0.0045 (0.12 vs 0.0045) | 0.2 vs 7.4e-10 (0.2 vs 7.4e-10) | 0.0006 vs <1e-12 (0.0006 vs <1e-12) |
| delta 0, alpha 0.005, cap 10 | 1.9e-05 vs 3.5e-06 (1.9e-05 vs 3.5e-06) | 0.062 vs 3.2e-09 (0.062 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.01 vs 0.0045 (0.01 vs 0.0045) | 0.022 vs 7.4e-10 (0.022 vs 7.4e-10) | 0.00064 vs <1e-12 (0.00064 vs <1e-12) |
| delta 0, alpha 0.005, cap 20 | 2.4e-06 vs 3.5e-06 (2.4e-06 vs 3.5e-06) | 0.16 vs 3.2e-09 (0.16 vs 3.2e-09) | 0.048 vs 0.15 (0.048 vs 0.15) | 0.032 vs 0.0045 (0.032 vs 0.0045) | 0.056 vs 7.4e-10 (0.056 vs 7.4e-10) | 0.00045 vs <1e-12 (0.00045 vs <1e-12) |
| delta 0, alpha 0.005, cap 30 | 3.2e-07 vs 3.5e-06 (3.2e-07 vs 3.5e-06) | 0.28 vs 3.2e-09 (0.28 vs 3.2e-09) | 0.1 vs 0.15 (0.1 vs 0.15) | 0.056 vs 0.0045 (0.056 vs 0.0045) | 0.097 vs 7.4e-10 (0.097 vs 7.4e-10) | 0.0003 vs <1e-12 (0.0003 vs <1e-12) |
| delta 0, alpha 0.005, cap 40 | 3e-07 vs 3.5e-06 (3e-07 vs 3.5e-06) | 0.41 vs 3.2e-09 (0.41 vs 3.2e-09) | 0.17 vs 0.15 (0.17 vs 0.15) | 0.082 vs 0.0045 (0.082 vs 0.0045) | 0.14 vs 7.4e-10 (0.14 vs 7.4e-10) | 0.00024 vs <1e-12 (0.00024 vs <1e-12) |
| delta 0, alpha 0.003, cap 10 | 2.3e-06 vs 3.5e-06 (2.3e-06 vs 3.5e-06) | 0.044 vs 3.2e-09 (0.044 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0064 vs 0.0045 (0.0064 vs 0.0045) | 0.014 vs 7.4e-10 (0.014 vs 7.4e-10) | 0.00026 vs <1e-12 (0.00026 vs <1e-12) |
| delta 0, alpha 0.003, cap 20 | 3e-07 vs 3.5e-06 (3e-07 vs 3.5e-06) | 0.14 vs 3.2e-09 (0.14 vs 3.2e-09) | 0.04 vs 0.15 (0.04 vs 0.15) | 0.025 vs 0.0045 (0.025 vs 0.0045) | 0.045 vs 7.4e-10 (0.045 vs 7.4e-10) | 0.00021 vs <1e-12 (0.00021 vs <1e-12) |
| delta 0, alpha 0.003, cap 30 | 4.1e-08 vs 3.5e-06 (4.1e-08 vs 3.5e-06) | 0.22 vs 3.2e-09 (0.22 vs 3.2e-09) | 0.074 vs 0.15 (0.074 vs 0.15) | 0.038 vs 0.0045 (0.038 vs 0.0045) | 0.068 vs 7.4e-10 (0.068 vs 7.4e-10) | 0.00013 vs <1e-12 (0.00013 vs <1e-12) |
| delta 0, alpha 0.003, cap 40 | 3.7e-08 vs 3.5e-06 (3.7e-08 vs 3.5e-06) | 0.33 vs 3.2e-09 (0.33 vs 3.2e-09) | 0.12 vs 0.15 (0.12 vs 0.15) | 0.057 vs 0.0045 (0.057 vs 0.0045) | 0.1 vs 7.4e-10 (0.1 vs 7.4e-10) | 0.00011 vs <1e-12 (0.00011 vs <1e-12) |
| delta 0, alpha 0.002, cap 10 | 2.3e-06 vs 3.5e-06 (2.3e-06 vs 3.5e-06) | 0.044 vs 3.2e-09 (0.044 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0064 vs 0.0045 (0.0064 vs 0.0045) | 0.014 vs 7.4e-10 (0.014 vs 7.4e-10) | 0.00026 vs <1e-12 (0.00026 vs <1e-12) |
| delta 0, alpha 0.002, cap 20 | 2.9e-07 vs 3.5e-06 (2.9e-07 vs 3.5e-06) | 0.09 vs 3.2e-09 (0.09 vs 3.2e-09) | 0.018 vs 0.15 (0.018 vs 0.15) | 0.014 vs 0.0045 (0.014 vs 0.0045) | 0.027 vs 7.4e-10 (0.027 vs 7.4e-10) | 0.00016 vs <1e-12 (0.00016 vs <1e-12) |
| delta 0, alpha 0.002, cap 30 | 3.7e-08 vs 3.5e-06 (3.7e-08 vs 3.5e-06) | 0.21 vs 3.2e-09 (0.21 vs 3.2e-09) | 0.064 vs 0.15 (0.064 vs 0.15) | 0.032 vs 0.0045 (0.032 vs 0.0045) | 0.06 vs 7.4e-10 (0.06 vs 7.4e-10) | 9.2e-05 vs <1e-12 (9.2e-05 vs <1e-12) |
| delta 0, alpha 0.002, cap 40 | 4.6e-09 vs 3.5e-06 (4.6e-09 vs 3.5e-06) | 0.28 vs 3.2e-09 (0.28 vs 3.2e-09) | 0.091 vs 0.15 (0.091 vs 0.15) | 0.04 vs 0.0045 (0.04 vs 0.0045) | 0.077 vs 7.4e-10 (0.077 vs 7.4e-10) | 4.9e-05 vs <1e-12 (4.9e-05 vs <1e-12) |
| delta 0, alpha 0.001, cap 10 | 2.9e-07 vs 3.5e-06 (2.9e-07 vs 3.5e-06) | 0.031 vs 3.2e-09 (0.031 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0039 vs 0.0045 (0.0039 vs 0.0045) | 0.009 vs 7.4e-10 (0.009 vs 7.4e-10) | 0.0001 vs <1e-12 (0.0001 vs <1e-12) |
| delta 0, alpha 0.001, cap 20 | 4.6e-09 vs 3.5e-06 (4.6e-09 vs 3.5e-06) | 0.06 vs 3.2e-09 (0.06 vs 3.2e-09) | 0.011 vs 0.15 (0.011 vs 0.15) | 0.0074 vs 0.0045 (0.0074 vs 0.0045) | 0.015 vs 7.4e-10 (0.015 vs 7.4e-10) | 3.3e-05 vs <1e-12 (3.3e-05 vs <1e-12) |
| delta 0, alpha 0.001, cap 30 | 4.6e-09 vs 3.5e-06 (4.6e-09 vs 3.5e-06) | 0.13 vs 3.2e-09 (0.13 vs 3.2e-09) | 0.034 vs 0.15 (0.034 vs 0.15) | 0.017 vs 0.0045 (0.017 vs 0.0045) | 0.034 vs 7.4e-10 (0.034 vs 7.4e-10) | 3.8e-05 vs <1e-12 (3.8e-05 vs <1e-12) |
| delta 0, alpha 0.001, cap 40 | 4.6e-09 vs 3.5e-06 (4.6e-09 vs 3.5e-06) | 0.21 vs 3.2e-09 (0.21 vs 3.2e-09) | 0.059 vs 0.15 (0.059 vs 0.15) | 0.025 vs 0.0045 (0.025 vs 0.0045) | 0.051 vs 7.4e-10 (0.051 vs 7.4e-10) | 3.4e-05 vs <1e-12 (3.4e-05 vs <1e-12) |
| delta 0, alpha 0.0001, cap 20 | 7.1e-11 vs 3.5e-06 (7.1e-11 vs 3.5e-06) | 0.015 vs 3.2e-09 (0.015 vs 3.2e-09) | 0.001 vs 0.15 (0.001 vs 0.15) | 0.0011 vs 0.0045 (0.0011 vs 0.0045) | 0.0029 vs 7.4e-10 (0.0029 vs 7.4e-10) | 3.4e-06 vs <1e-12 (3.4e-06 vs <1e-12) |
| delta 0, alpha 0.0001, cap 30 | 8.9e-12 vs 3.5e-06 (8.9e-12 vs 3.5e-06) | 0.044 vs 3.2e-09 (0.044 vs 3.2e-09) | 0.0068 vs 0.15 (0.0068 vs 0.15) | 0.003 vs 0.0045 (0.003 vs 0.0045) | 0.0074 vs 7.4e-10 (0.0074 vs 7.4e-10) | 1.9e-06 vs <1e-12 (1.9e-06 vs <1e-12) |
| delta 0, alpha 0.0001, cap 40 | 1.1e-12 vs 3.5e-06 (1.1e-12 vs 3.5e-06) | 0.082 vs 3.2e-09 (0.082 vs 3.2e-09) | 0.015 vs 0.15 (0.015 vs 0.15) | 0.0053 vs 0.0045 (0.0053 vs 0.0045) | 0.013 vs 7.4e-10 (0.013 vs 7.4e-10) | 1.2e-06 vs <1e-12 (1.2e-06 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 10 | 0.0096 vs 3.5e-06 (0.0096 vs 3.5e-06) | 0.015 vs 3.2e-09 (0.015 vs 3.2e-09) | 0.054 vs 0.15 (0.054 vs 0.15) | 0.059 vs 0.0045 (0.059 vs 0.0045) | 0.027 vs 7.4e-10 (0.027 vs 7.4e-10) | 0.00012 vs <1e-12 (0.00012 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 20 | 0.0012 vs 3.5e-06 (0.0012 vs 3.5e-06) | 0.015 vs 3.2e-09 (0.015 vs 3.2e-09) | 0.17 vs 0.15 (0.17 vs 0.15) | 0.1 vs 0.0045 (0.1 vs 0.0045) | 0.049 vs 7.4e-10 (0.049 vs 7.4e-10) | 2.3e-05 vs <1e-12 (2.3e-05 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 30 | 0.0012 vs 3.5e-06 (0.0012 vs 3.5e-06) | 0.015 vs 3.2e-09 (0.015 vs 3.2e-09) | 0.25 vs 0.15 (0.25 vs 0.15) | 0.14 vs 0.0045 (0.14 vs 0.0045) | 0.062 vs 7.4e-10 (0.062 vs 7.4e-10) | 2.1e-05 vs <1e-12 (2.1e-05 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 40 | 0.00016 vs 3.5e-06 (0.00016 vs 3.5e-06) | 0.013 vs 3.2e-09 (0.013 vs 3.2e-09) | 0.33 vs 0.15 (0.33 vs 0.15) | 0.17 vs 0.0045 (0.17 vs 0.0045) | 0.071 vs 7.4e-10 (0.071 vs 7.4e-10) | 4e-06 vs <1e-12 (4e-06 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 10 | 0.00016 vs 3.5e-06 (0.00016 vs 3.5e-06) | 0.0044 vs 3.2e-09 (0.0044 vs 3.2e-09) | 0.033 vs 0.15 (0.033 vs 0.15) | 0.029 vs 0.0045 (0.029 vs 0.0045) | 0.012 vs 7.4e-10 (0.012 vs 7.4e-10) | 3.9e-06 vs <1e-12 (3.9e-06 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 20 | 0.00015 vs 3.5e-06 (0.00015 vs 3.5e-06) | 0.005 vs 3.2e-09 (0.005 vs 3.2e-09) | 0.086 vs 0.15 (0.086 vs 0.15) | 0.051 vs 0.0045 (0.051 vs 0.0045) | 0.02 vs 7.4e-10 (0.02 vs 7.4e-10) | 3.5e-06 vs <1e-12 (3.5e-06 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 30 | 2e-05 vs 3.5e-06 (2e-05 vs 3.5e-06) | 0.0047 vs 3.2e-09 (0.0047 vs 3.2e-09) | 0.14 vs 0.15 (0.14 vs 0.15) | 0.071 vs 0.0045 (0.071 vs 0.0045) | 0.026 vs 7.4e-10 (0.026 vs 7.4e-10) | 6.8e-07 vs <1e-12 (6.8e-07 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 40 | 2e-05 vs 3.5e-06 (2e-05 vs 3.5e-06) | 0.0043 vs 3.2e-09 (0.0043 vs 3.2e-09) | 0.19 vs 0.15 (0.19 vs 0.15) | 0.089 vs 0.0045 (0.089 vs 0.0045) | 0.03 vs 7.4e-10 (0.03 vs 7.4e-10) | 6.7e-07 vs <1e-12 (6.7e-07 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 10 | 0.00015 vs 3.5e-06 (0.00015 vs 3.5e-06) | 0.0022 vs 3.2e-09 (0.0022 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.011 vs 0.0045 (0.011 vs 0.0045) | 0.0036 vs 7.4e-10 (0.0036 vs 7.4e-10) | 3.3e-06 vs <1e-12 (3.3e-06 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 20 | 1.9e-05 vs 3.5e-06 (1.9e-05 vs 3.5e-06) | 0.0022 vs 3.2e-09 (0.0022 vs 3.2e-09) | 0.046 vs 0.15 (0.046 vs 0.15) | 0.027 vs 0.0045 (0.027 vs 0.0045) | 0.0096 vs 7.4e-10 (0.0096 vs 7.4e-10) | 5.8e-07 vs <1e-12 (5.8e-07 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 30 | 2.5e-06 vs 3.5e-06 (2.5e-06 vs 3.5e-06) | 0.002 vs 3.2e-09 (0.002 vs 3.2e-09) | 0.095 vs 0.15 (0.095 vs 0.15) | 0.044 vs 0.0045 (0.044 vs 0.0045) | 0.014 vs 7.4e-10 (0.014 vs 7.4e-10) | 1.1e-07 vs <1e-12 (1.1e-07 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 40 | 2.4e-06 vs 3.5e-06 (2.4e-06 vs 3.5e-06) | 0.0018 vs 3.2e-09 (0.0018 vs 3.2e-09) | 0.13 vs 0.15 (0.13 vs 0.15) | 0.053 vs 0.0045 (0.053 vs 0.0045) | 0.016 vs 7.4e-10 (0.016 vs 7.4e-10) | 9.7e-08 vs <1e-12 (9.7e-08 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 10 | 1.9e-05 vs 3.5e-06 (1.9e-05 vs 3.5e-06) | 0.00097 vs 3.2e-09 (0.00097 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0063 vs 0.0045 (0.0063 vs 0.0045) | 0.0019 vs 7.4e-10 (0.0019 vs 7.4e-10) | 5.6e-07 vs <1e-12 (5.6e-07 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 20 | 2.4e-06 vs 3.5e-06 (2.4e-06 vs 3.5e-06) | 0.00099 vs 3.2e-09 (0.00099 vs 3.2e-09) | 0.026 vs 0.15 (0.026 vs 0.15) | 0.015 vs 0.0045 (0.015 vs 0.0045) | 0.0049 vs 7.4e-10 (0.0049 vs 7.4e-10) | 9.7e-08 vs <1e-12 (9.7e-08 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 30 | 3.2e-07 vs 3.5e-06 (3.2e-07 vs 3.5e-06) | 0.00088 vs 3.2e-09 (0.00088 vs 3.2e-09) | 0.055 vs 0.15 (0.055 vs 0.15) | 0.024 vs 0.0045 (0.024 vs 0.0045) | 0.007 vs 7.4e-10 (0.007 vs 7.4e-10) | 1.9e-08 vs <1e-12 (1.9e-08 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 40 | 3e-07 vs 3.5e-06 (3e-07 vs 3.5e-06) | 0.00077 vs 3.2e-09 (0.00077 vs 3.2e-09) | 0.082 vs 0.15 (0.082 vs 0.15) | 0.032 vs 0.0045 (0.032 vs 0.0045) | 0.0083 vs 7.4e-10 (0.0083 vs 7.4e-10) | 1.6e-08 vs <1e-12 (1.6e-08 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 10 | 2.3e-06 vs 3.5e-06 (2.3e-06 vs 3.5e-06) | 0.00043 vs 3.2e-09 (0.00043 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0036 vs 0.0045 (0.0036 vs 0.0045) | 0.001 vs 7.4e-10 (0.001 vs 7.4e-10) | 9.3e-08 vs <1e-12 (9.3e-08 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 20 | 3e-07 vs 3.5e-06 (3e-07 vs 3.5e-06) | 0.00053 vs 3.2e-09 (0.00053 vs 3.2e-09) | 0.021 vs 0.15 (0.021 vs 0.15) | 0.011 vs 0.0045 (0.011 vs 0.0045) | 0.0033 vs 7.4e-10 (0.0033 vs 7.4e-10) | 1.6e-08 vs <1e-12 (1.6e-08 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 30 | 4.1e-08 vs 3.5e-06 (4.1e-08 vs 3.5e-06) | 0.00041 vs 3.2e-09 (0.00041 vs 3.2e-09) | 0.036 vs 0.15 (0.036 vs 0.15) | 0.015 vs 0.0045 (0.015 vs 0.0045) | 0.0039 vs 7.4e-10 (0.0039 vs 7.4e-10) | 3.3e-09 vs <1e-12 (3.3e-09 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 40 | 3.7e-08 vs 3.5e-06 (3.7e-08 vs 3.5e-06) | 0.0004 vs 3.2e-09 (0.0004 vs 3.2e-09) | 0.057 vs 0.15 (0.057 vs 0.15) | 0.021 vs 0.0045 (0.021 vs 0.0045) | 0.0051 vs 7.4e-10 (0.0051 vs 7.4e-10) | 2.7e-09 vs <1e-12 (2.7e-09 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 10 | 2.3e-06 vs 3.5e-06 (2.3e-06 vs 3.5e-06) | 0.00043 vs 3.2e-09 (0.00043 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0036 vs 0.0045 (0.0036 vs 0.0045) | 0.001 vs 7.4e-10 (0.001 vs 7.4e-10) | 9.3e-08 vs <1e-12 (9.3e-08 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 20 | 2.9e-07 vs 3.5e-06 (2.9e-07 vs 3.5e-06) | 0.00036 vs 3.2e-09 (0.00036 vs 3.2e-09) | 0.0094 vs 0.15 (0.0094 vs 0.15) | 0.0063 vs 0.0045 (0.0063 vs 0.0045) | 0.0018 vs 7.4e-10 (0.0018 vs 7.4e-10) | 1.6e-08 vs <1e-12 (1.6e-08 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 30 | 3.7e-08 vs 3.5e-06 (3.7e-08 vs 3.5e-06) | 0.00029 vs 3.2e-09 (0.00029 vs 3.2e-09) | 0.03 vs 0.15 (0.03 vs 0.15) | 0.012 vs 0.0045 (0.012 vs 0.0045) | 0.003 vs 7.4e-10 (0.003 vs 7.4e-10) | 2.7e-09 vs <1e-12 (2.7e-09 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 40 | 4.6e-09 vs 3.5e-06 (4.6e-09 vs 3.5e-06) | 0.0002 vs 3.2e-09 (0.0002 vs 3.2e-09) | 0.04 vs 0.15 (0.04 vs 0.15) | 0.014 vs 0.0045 (0.014 vs 0.0045) | 0.003 vs 7.4e-10 (0.003 vs 7.4e-10) | 4.6e-10 vs <1e-12 (4.6e-10 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 10 | 2.9e-07 vs 3.5e-06 (2.9e-07 vs 3.5e-06) | 0.00019 vs 3.2e-09 (0.00019 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0021 vs 0.0045 (0.0021 vs 0.0045) | 0.00053 vs 7.4e-10 (0.00053 vs 7.4e-10) | 1.6e-08 vs <1e-12 (1.6e-08 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 20 | 4.6e-09 vs 3.5e-06 (4.6e-09 vs 3.5e-06) | 9.6e-05 vs 3.2e-09 (9.6e-05 vs 3.2e-09) | 0.0051 vs 0.15 (0.0051 vs 0.15) | 0.0029 vs 0.0045 (0.0029 vs 0.0045) | 0.00072 vs 7.4e-10 (0.00072 vs 7.4e-10) | 4.6e-10 vs <1e-12 (4.6e-10 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 30 | 4.6e-09 vs 3.5e-06 (4.6e-09 vs 3.5e-06) | 0.00013 vs 3.2e-09 (0.00013 vs 3.2e-09) | 0.015 vs 0.15 (0.015 vs 0.15) | 0.0061 vs 0.0045 (0.0061 vs 0.0045) | 0.0014 vs 7.4e-10 (0.0014 vs 7.4e-10) | 4.6e-10 vs <1e-12 (4.6e-10 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 40 | 4.6e-09 vs 3.5e-06 (4.6e-09 vs 3.5e-06) | 0.00012 vs 3.2e-09 (0.00012 vs 3.2e-09) | 0.024 vs 0.15 (0.024 vs 0.15) | 0.0081 vs 0.0045 (0.0081 vs 0.0045) | 0.0017 vs 7.4e-10 (0.0017 vs 7.4e-10) | 4.5e-10 vs <1e-12 (4.5e-10 vs <1e-12) |
| delta 0.01, alpha 0.0001, cap 20 | 7.1e-11 vs 3.5e-06 (7.1e-11 vs 3.5e-06) | 1e-05 vs 3.2e-09 (1e-05 vs 3.2e-09) | 0.00041 vs 0.15 (0.00041 vs 0.15) | 0.00042 vs 0.0045 (0.00042 vs 0.0045) | 7.8e-05 vs 7.4e-10 (7.8e-05 vs 7.4e-10) | 1.2e-11 vs <1e-12 (1.2e-11 vs <1e-12) |
| delta 0.01, alpha 0.0001, cap 30 | 8.9e-12 vs 3.5e-06 (8.9e-12 vs 3.5e-06) | 8.3e-06 vs 3.2e-09 (8.3e-06 vs 3.2e-09) | 0.0024 vs 0.15 (0.0024 vs 0.15) | 0.00086 vs 0.0045 (0.00086 vs 0.0045) | 0.00014 vs 7.4e-10 (0.00014 vs 7.4e-10) | 2e-12 vs <1e-12 (2e-12 vs <1e-12) |
| delta 0.01, alpha 0.0001, cap 40 | 1.1e-12 vs 3.5e-06 (1.1e-12 vs 3.5e-06) | 6.7e-06 vs 3.2e-09 (6.7e-06 vs 3.2e-09) | 0.0049 vs 0.15 (0.0049 vs 0.15) | 0.0013 vs 0.0045 (0.0013 vs 0.0045) | 0.00019 vs 7.4e-10 (0.00019 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 10 | 0.0039 vs 3.5e-06 (0.0039 vs 3.5e-06) | 0.005 vs 3.2e-09 (0.005 vs 3.2e-09) | 0.048 vs 0.15 (0.048 vs 0.15) | 0.051 vs 0.0045 (0.051 vs 0.0045) | 0.012 vs 7.4e-10 (0.012 vs 7.4e-10) | 8.2e-06 vs <1e-12 (8.2e-06 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 20 | 0.00033 vs 3.5e-06 (0.00033 vs 3.5e-06) | 0.0038 vs 3.2e-09 (0.0038 vs 3.2e-09) | 0.15 vs 0.15 (0.15 vs 0.15) | 0.087 vs 0.0045 (0.087 vs 0.0045) | 0.023 vs 7.4e-10 (0.023 vs 7.4e-10) | 8.4e-07 vs <1e-12 (8.4e-07 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 30 | 0.00032 vs 3.5e-06 (0.00032 vs 3.5e-06) | 0.0031 vs 3.2e-09 (0.0031 vs 3.2e-09) | 0.22 vs 0.15 (0.22 vs 0.15) | 0.12 vs 0.0045 (0.12 vs 0.0045) | 0.026 vs 7.4e-10 (0.026 vs 7.4e-10) | 8e-07 vs <1e-12 (8e-07 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 40 | 2.8e-05 vs 3.5e-06 (2.8e-05 vs 3.5e-06) | 0.0021 vs 3.2e-09 (0.0021 vs 3.2e-09) | 0.28 vs 0.15 (0.28 vs 0.15) | 0.14 vs 0.0045 (0.14 vs 0.0045) | 0.027 vs 7.4e-10 (0.027 vs 7.4e-10) | 8.3e-08 vs <1e-12 (8.3e-08 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 10 | 2.7e-05 vs 3.5e-06 (2.7e-05 vs 3.5e-06) | 0.0011 vs 3.2e-09 (0.0011 vs 3.2e-09) | 0.029 vs 0.15 (0.029 vs 0.15) | 0.024 vs 0.0045 (0.024 vs 0.0045) | 0.0049 vs 7.4e-10 (0.0049 vs 7.4e-10) | 8.2e-08 vs <1e-12 (8.2e-08 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 20 | 2.7e-05 vs 3.5e-06 (2.7e-05 vs 3.5e-06) | 0.001 vs 3.2e-09 (0.001 vs 3.2e-09) | 0.073 vs 0.15 (0.073 vs 0.15) | 0.04 vs 0.0045 (0.04 vs 0.0045) | 0.0075 vs 7.4e-10 (0.0075 vs 7.4e-10) | 7.8e-08 vs <1e-12 (7.8e-08 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 30 | 2.3e-06 vs 3.5e-06 (2.3e-06 vs 3.5e-06) | 0.00073 vs 3.2e-09 (0.00073 vs 3.2e-09) | 0.12 vs 0.15 (0.12 vs 0.15) | 0.055 vs 0.0045 (0.055 vs 0.0045) | 0.0095 vs 7.4e-10 (0.0095 vs 7.4e-10) | 8.1e-09 vs <1e-12 (8.1e-09 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 40 | 2.3e-06 vs 3.5e-06 (2.3e-06 vs 3.5e-06) | 0.0006 vs 3.2e-09 (0.0006 vs 3.2e-09) | 0.16 vs 0.15 (0.16 vs 0.15) | 0.068 vs 0.0045 (0.068 vs 0.0045) | 0.0097 vs 7.4e-10 (0.0097 vs 7.4e-10) | 8.1e-09 vs <1e-12 (8.1e-09 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 10 | 2.7e-05 vs 3.5e-06 (2.7e-05 vs 3.5e-06) | 0.00056 vs 3.2e-09 (0.00056 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0094 vs 0.0045 (0.0094 vs 0.0045) | 0.0012 vs 7.4e-10 (0.0012 vs 7.4e-10) | 7.8e-08 vs <1e-12 (7.8e-08 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 20 | 2.2e-06 vs 3.5e-06 (2.2e-06 vs 3.5e-06) | 0.00038 vs 3.2e-09 (0.00038 vs 3.2e-09) | 0.038 vs 0.15 (0.038 vs 0.15) | 0.021 vs 0.0045 (0.021 vs 0.0045) | 0.0034 vs 7.4e-10 (0.0034 vs 7.4e-10) | 7.6e-09 vs <1e-12 (7.6e-09 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 30 | 1.9e-07 vs 3.5e-06 (1.9e-07 vs 3.5e-06) | 0.00025 vs 3.2e-09 (0.00025 vs 3.2e-09) | 0.077 vs 0.15 (0.077 vs 0.15) | 0.033 vs 0.0045 (0.033 vs 0.0045) | 0.0045 vs 7.4e-10 (0.0045 vs 7.4e-10) | 7.9e-10 vs <1e-12 (7.9e-10 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 40 | 1.9e-07 vs 3.5e-06 (1.9e-07 vs 3.5e-06) | 0.00019 vs 3.2e-09 (0.00019 vs 3.2e-09) | 0.1 vs 0.15 (0.1 vs 0.15) | 0.039 vs 0.0045 (0.039 vs 0.0045) | 0.0045 vs 7.4e-10 (0.0045 vs 7.4e-10) | 7.4e-10 vs <1e-12 (7.4e-10 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 10 | 2.2e-06 vs 3.5e-06 (2.2e-06 vs 3.5e-06) | 0.00021 vs 3.2e-09 (0.00021 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0053 vs 0.0045 (0.0053 vs 0.0045) | 0.00057 vs 7.4e-10 (0.00057 vs 7.4e-10) | 7.5e-09 vs <1e-12 (7.5e-09 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 20 | 1.9e-07 vs 3.5e-06 (1.9e-07 vs 3.5e-06) | 0.00014 vs 3.2e-09 (0.00014 vs 3.2e-09) | 0.021 vs 0.15 (0.021 vs 0.15) | 0.012 vs 0.0045 (0.012 vs 0.0045) | 0.0015 vs 7.4e-10 (0.0015 vs 7.4e-10) | 7.4e-10 vs <1e-12 (7.4e-10 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 30 | 1.6e-08 vs 3.5e-06 (1.6e-08 vs 3.5e-06) | 9.4e-05 vs 3.2e-09 (9.4e-05 vs 3.2e-09) | 0.043 vs 0.15 (0.043 vs 0.15) | 0.018 vs 0.0045 (0.018 vs 0.0045) | 0.002 vs 7.4e-10 (0.002 vs 7.4e-10) | 7.7e-11 vs <1e-12 (7.7e-11 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 40 | 1.6e-08 vs 3.5e-06 (1.6e-08 vs 3.5e-06) | 7.2e-05 vs 3.2e-09 (7.2e-05 vs 3.2e-09) | 0.064 vs 0.15 (0.064 vs 0.15) | 0.022 vs 0.0045 (0.022 vs 0.0045) | 0.0021 vs 7.4e-10 (0.0021 vs 7.4e-10) | 7.2e-11 vs <1e-12 (7.2e-11 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 10 | 1.9e-07 vs 3.5e-06 (1.9e-07 vs 3.5e-06) | 8e-05 vs 3.2e-09 (8e-05 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0029 vs 0.0045 (0.0029 vs 0.0045) | 0.00027 vs 7.4e-10 (0.00027 vs 7.4e-10) | 7.3e-10 vs <1e-12 (7.3e-10 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 20 | 1.6e-08 vs 3.5e-06 (1.6e-08 vs 3.5e-06) | 6.2e-05 vs 3.2e-09 (6.2e-05 vs 3.2e-09) | 0.017 vs 0.15 (0.017 vs 0.15) | 0.0083 vs 0.0045 (0.0083 vs 0.0045) | 0.00096 vs 7.4e-10 (0.00096 vs 7.4e-10) | 7.2e-11 vs <1e-12 (7.2e-11 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 30 | 1.4e-09 vs 3.5e-06 (1.4e-09 vs 3.5e-06) | 3.8e-05 vs 3.2e-09 (3.8e-05 vs 3.2e-09) | 0.028 vs 0.15 (0.028 vs 0.15) | 0.01 vs 0.0045 (0.01 vs 0.0045) | 0.001 vs 7.4e-10 (0.001 vs 7.4e-10) | 7.6e-12 vs <1e-12 (7.6e-12 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 40 | 1.3e-09 vs 3.5e-06 (1.3e-09 vs 3.5e-06) | 3.1e-05 vs 3.2e-09 (3.1e-05 vs 3.2e-09) | 0.043 vs 0.15 (0.043 vs 0.15) | 0.014 vs 0.0045 (0.014 vs 0.0045) | 0.0012 vs 7.4e-10 (0.0012 vs 7.4e-10) | 7e-12 vs <1e-12 (7e-12 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 10 | 1.9e-07 vs 3.5e-06 (1.9e-07 vs 3.5e-06) | 8e-05 vs 3.2e-09 (8e-05 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0029 vs 0.0045 (0.0029 vs 0.0045) | 0.00027 vs 7.4e-10 (0.00027 vs 7.4e-10) | 7.3e-10 vs <1e-12 (7.3e-10 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 20 | 1.6e-08 vs 3.5e-06 (1.6e-08 vs 3.5e-06) | 4.8e-05 vs 3.2e-09 (4.8e-05 vs 3.2e-09) | 0.0074 vs 0.15 (0.0074 vs 0.15) | 0.0048 vs 0.0045 (0.0048 vs 0.0045) | 0.00051 vs 7.4e-10 (0.00051 vs 7.4e-10) | 7.2e-11 vs <1e-12 (7.2e-11 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 30 | 1.3e-09 vs 3.5e-06 (1.3e-09 vs 3.5e-06) | 2.6e-05 vs 3.2e-09 (2.6e-05 vs 3.2e-09) | 0.023 vs 0.15 (0.023 vs 0.15) | 0.0084 vs 0.0045 (0.0084 vs 0.0045) | 0.00072 vs 7.4e-10 (0.00072 vs 7.4e-10) | 7e-12 vs <1e-12 (7e-12 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 40 | 1.1e-10 vs 3.5e-06 (1.1e-10 vs 3.5e-06) | 1.3e-05 vs 3.2e-09 (1.3e-05 vs 3.2e-09) | 0.03 vs 0.15 (0.03 vs 0.15) | 0.0092 vs 0.0045 (0.0092 vs 0.0045) | 0.00065 vs 7.4e-10 (0.00065 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 10 | 1.6e-08 vs 3.5e-06 (1.6e-08 vs 3.5e-06) | 3e-05 vs 3.2e-09 (3e-05 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0016 vs 0.0045 (0.0016 vs 0.0045) | 0.00013 vs 7.4e-10 (0.00013 vs 7.4e-10) | 7.1e-11 vs <1e-12 (7.1e-11 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 20 | 1.1e-10 vs 3.5e-06 (1.1e-10 vs 3.5e-06) | 8.6e-06 vs 3.2e-09 (8.6e-06 vs 3.2e-09) | 0.004 vs 0.15 (0.004 vs 0.15) | 0.0021 vs 0.0045 (0.0021 vs 0.0045) | 0.00018 vs 7.4e-10 (0.00018 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 30 | 1.1e-10 vs 3.5e-06 (1.1e-10 vs 3.5e-06) | 9.9e-06 vs 3.2e-09 (9.9e-06 vs 3.2e-09) | 0.011 vs 0.15 (0.011 vs 0.15) | 0.0042 vs 0.0045 (0.0042 vs 0.0045) | 0.00032 vs 7.4e-10 (0.00032 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 40 | 1.1e-10 vs 3.5e-06 (1.1e-10 vs 3.5e-06) | 8.6e-06 vs 3.2e-09 (8.6e-06 vs 3.2e-09) | 0.018 vs 0.15 (0.018 vs 0.15) | 0.0054 vs 0.0045 (0.0054 vs 0.0045) | 0.00033 vs 7.4e-10 (0.00033 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.0001, cap 20 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | 7.6e-07 vs 3.2e-09 (7.6e-07 vs 3.2e-09) | 0.0003 vs 0.15 (0.0003 vs 0.15) | 0.00029 vs 0.0045 (0.00029 vs 0.0045) | 1.5e-05 vs 7.4e-10 (1.5e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.0001, cap 30 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | 3.9e-07 vs 3.2e-09 (3.9e-07 vs 3.2e-09) | 0.0017 vs 0.15 (0.0017 vs 0.15) | 0.00055 vs 0.0045 (0.00055 vs 0.0045) | 2.3e-05 vs 7.4e-10 (2.3e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.0001, cap 40 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | 2.2e-07 vs 3.2e-09 (2.2e-07 vs 3.2e-09) | 0.0033 vs 0.15 (0.0033 vs 0.15) | 0.00079 vs 0.0045 (0.00079 vs 0.0045) | 2.7e-05 vs 7.4e-10 (2.7e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 10 | 0.0034 vs 3.5e-06 (0.0034 vs 3.5e-06) | 0.00012 vs 3.2e-09 (0.00012 vs 3.2e-09) | 0.048 vs 0.15 (0.048 vs 0.15) | 0.044 vs 0.0045 (0.044 vs 0.0045) | 0.0039 vs 7.4e-10 (0.0039 vs 7.4e-10) | 4.5e-07 vs <1e-12 (4.5e-07 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 20 | 0.00029 vs 3.5e-06 (0.00029 vs 3.5e-06) | 0.0002 vs 3.2e-09 (0.0002 vs 3.2e-09) | 0.15 vs 0.15 (0.15 vs 0.15) | 0.072 vs 0.0045 (0.072 vs 0.0045) | 0.0047 vs 7.4e-10 (0.0047 vs 7.4e-10) | 2.5e-08 vs <1e-12 (2.5e-08 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 30 | 0.00029 vs 3.5e-06 (0.00029 vs 3.5e-06) | 9.4e-05 vs 3.2e-09 (9.4e-05 vs 3.2e-09) | 0.22 vs 0.15 (0.22 vs 0.15) | 0.093 vs 0.0045 (0.093 vs 0.0045) | 0.004 vs 7.4e-10 (0.004 vs 7.4e-10) | 2.5e-08 vs <1e-12 (2.5e-08 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 40 | 2.4e-05 vs 3.5e-06 (2.4e-05 vs 3.5e-06) | 7.7e-05 vs 3.2e-09 (7.7e-05 vs 3.2e-09) | 0.28 vs 0.15 (0.28 vs 0.15) | 0.11 vs 0.0045 (0.11 vs 0.0045) | 0.0032 vs 7.4e-10 (0.0032 vs 7.4e-10) | 1.4e-09 vs <1e-12 (1.4e-09 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 10 | 2.4e-05 vs 3.5e-06 (2.4e-05 vs 3.5e-06) | 3.4e-05 vs 3.2e-09 (3.4e-05 vs 3.2e-09) | 0.029 vs 0.15 (0.029 vs 0.15) | 0.02 vs 0.0045 (0.02 vs 0.0045) | 0.0011 vs 7.4e-10 (0.0011 vs 7.4e-10) | 1.4e-09 vs <1e-12 (1.4e-09 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 20 | 2.4e-05 vs 3.5e-06 (2.4e-05 vs 3.5e-06) | 2e-05 vs 3.2e-09 (2e-05 vs 3.2e-09) | 0.073 vs 0.15 (0.073 vs 0.15) | 0.032 vs 0.0045 (0.032 vs 0.0045) | 0.0011 vs 7.4e-10 (0.0011 vs 7.4e-10) | 1.4e-09 vs <1e-12 (1.4e-09 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 30 | 2.1e-06 vs 3.5e-06 (2.1e-06 vs 3.5e-06) | 2.1e-05 vs 3.2e-09 (2.1e-05 vs 3.2e-09) | 0.12 vs 0.15 (0.12 vs 0.15) | 0.043 vs 0.0045 (0.043 vs 0.0045) | 0.0011 vs 7.4e-10 (0.0011 vs 7.4e-10) | 7.8e-11 vs <1e-12 (7.8e-11 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 40 | 2.1e-06 vs 3.5e-06 (2.1e-06 vs 3.5e-06) | 1.4e-05 vs 3.2e-09 (1.4e-05 vs 3.2e-09) | 0.16 vs 0.15 (0.16 vs 0.15) | 0.05 vs 0.0045 (0.05 vs 0.0045) | 0.00089 vs 7.4e-10 (0.00089 vs 7.4e-10) | 7.8e-11 vs <1e-12 (7.8e-11 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 10 | 2.4e-05 vs 3.5e-06 (2.4e-05 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.008 vs 0.0045 (0.008 vs 0.0045) | 0.00037 vs 7.4e-10 (0.00037 vs 7.4e-10) | 1.4e-09 vs <1e-12 (1.4e-09 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 20 | 2e-06 vs 3.5e-06 (2e-06 vs 3.5e-06) | 5.9e-06 vs 3.2e-09 (5.9e-06 vs 3.2e-09) | 0.038 vs 0.15 (0.038 vs 0.15) | 0.017 vs 0.0045 (0.017 vs 0.0045) | 0.00046 vs 7.4e-10 (0.00046 vs 7.4e-10) | 7.7e-11 vs <1e-12 (7.7e-11 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 30 | 1.7e-07 vs 3.5e-06 (1.7e-07 vs 3.5e-06) | 4.7e-06 vs 3.2e-09 (4.7e-06 vs 3.2e-09) | 0.077 vs 0.15 (0.077 vs 0.15) | 0.024 vs 0.0045 (0.024 vs 0.0045) | 0.00039 vs 7.4e-10 (0.00039 vs 7.4e-10) | 4.4e-12 vs <1e-12 (4.4e-12 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 40 | 1.7e-07 vs 3.5e-06 (1.7e-07 vs 3.5e-06) | 2.2e-06 vs 3.2e-09 (2.2e-06 vs 3.2e-09) | 0.1 vs 0.15 (0.1 vs 0.15) | 0.028 vs 0.0045 (0.028 vs 0.0045) | 0.0003 vs 7.4e-10 (0.0003 vs 7.4e-10) | 4.3e-12 vs <1e-12 (4.3e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 10 | 2e-06 vs 3.5e-06 (2e-06 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0044 vs 0.0045 (0.0044 vs 0.0045) | 0.00015 vs 7.4e-10 (0.00015 vs 7.4e-10) | 7.7e-11 vs <1e-12 (7.7e-11 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 20 | 1.7e-07 vs 3.5e-06 (1.7e-07 vs 3.5e-06) | 1.6e-06 vs 3.2e-09 (1.6e-06 vs 3.2e-09) | 0.021 vs 0.15 (0.021 vs 0.15) | 0.0089 vs 0.0045 (0.0089 vs 0.0045) | 0.00018 vs 7.4e-10 (0.00018 vs 7.4e-10) | 4.3e-12 vs <1e-12 (4.3e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 30 | 1.4e-08 vs 3.5e-06 (1.4e-08 vs 3.5e-06) | 1.3e-06 vs 3.2e-09 (1.3e-06 vs 3.2e-09) | 0.043 vs 0.15 (0.043 vs 0.15) | 0.013 vs 0.0045 (0.013 vs 0.0045) | 0.00015 vs 7.4e-10 (0.00015 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 40 | 1.4e-08 vs 3.5e-06 (1.4e-08 vs 3.5e-06) | 6.5e-07 vs 3.2e-09 (6.5e-07 vs 3.2e-09) | 0.064 vs 0.15 (0.064 vs 0.15) | 0.016 vs 0.0045 (0.016 vs 0.0045) | 0.00012 vs 7.4e-10 (0.00012 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 10 | 1.7e-07 vs 3.5e-06 (1.7e-07 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0024 vs 0.0045 (0.0024 vs 0.0045) | 5.9e-05 vs 7.4e-10 (5.9e-05 vs 7.4e-10) | 4.3e-12 vs <1e-12 (4.3e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 20 | 1.4e-08 vs 3.5e-06 (1.4e-08 vs 3.5e-06) | 5.9e-07 vs 3.2e-09 (5.9e-07 vs 3.2e-09) | 0.017 vs 0.15 (0.017 vs 0.15) | 0.0062 vs 0.0045 (0.0062 vs 0.0045) | 8.5e-05 vs 7.4e-10 (8.5e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 30 | 1.2e-09 vs 3.5e-06 (1.2e-09 vs 3.5e-06) | 4e-07 vs 3.2e-09 (4e-07 vs 3.2e-09) | 0.028 vs 0.15 (0.028 vs 0.15) | 0.0074 vs 0.0045 (0.0074 vs 0.0045) | 6.2e-05 vs 7.4e-10 (6.2e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 40 | 1.2e-09 vs 3.5e-06 (1.2e-09 vs 3.5e-06) | 2.2e-07 vs 3.2e-09 (2.2e-07 vs 3.2e-09) | 0.043 vs 0.15 (0.043 vs 0.15) | 0.0098 vs 0.0045 (0.0098 vs 0.0045) | 5.5e-05 vs 7.4e-10 (5.5e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 10 | 1.7e-07 vs 3.5e-06 (1.7e-07 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0024 vs 0.0045 (0.0024 vs 0.0045) | 5.9e-05 vs 7.4e-10 (5.9e-05 vs 7.4e-10) | 4.3e-12 vs <1e-12 (4.3e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 20 | 1.4e-08 vs 3.5e-06 (1.4e-08 vs 3.5e-06) | 3.3e-07 vs 3.2e-09 (3.3e-07 vs 3.2e-09) | 0.0074 vs 0.15 (0.0074 vs 0.15) | 0.0036 vs 0.0045 (0.0036 vs 0.0045) | 5.5e-05 vs 7.4e-10 (5.5e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 30 | 1.2e-09 vs 3.5e-06 (1.2e-09 vs 3.5e-06) | 1.7e-07 vs 3.2e-09 (1.7e-07 vs 3.2e-09) | 0.023 vs 0.15 (0.023 vs 0.15) | 0.0058 vs 0.0045 (0.0058 vs 0.0045) | 4e-05 vs 7.4e-10 (4e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 40 | 9.6e-11 vs 3.5e-06 (9.6e-11 vs 3.5e-06) | 7e-08 vs 3.2e-09 (7e-08 vs 3.2e-09) | 0.03 vs 0.15 (0.03 vs 0.15) | 0.0061 vs 0.0045 (0.0061 vs 0.0045) | 2.4e-05 vs 7.4e-10 (2.4e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 10 | 1.4e-08 vs 3.5e-06 (1.4e-08 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0013 vs 0.0045 (0.0013 vs 0.0045) | 2.4e-05 vs 7.4e-10 (2.4e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 20 | 9.6e-11 vs 3.5e-06 (9.6e-11 vs 3.5e-06) | 4.5e-08 vs 3.2e-09 (4.5e-08 vs 3.2e-09) | 0.004 vs 0.15 (0.004 vs 0.15) | 0.0015 vs 0.0045 (0.0015 vs 0.0045) | 1.2e-05 vs 7.4e-10 (1.2e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 30 | 9.6e-11 vs 3.5e-06 (9.6e-11 vs 3.5e-06) | 5.2e-08 vs 3.2e-09 (5.2e-08 vs 3.2e-09) | 0.011 vs 0.15 (0.011 vs 0.15) | 0.0029 vs 0.0045 (0.0029 vs 0.0045) | 1.6e-05 vs 7.4e-10 (1.6e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 40 | 9.6e-11 vs 3.5e-06 (9.6e-11 vs 3.5e-06) | 3.6e-08 vs 3.2e-09 (3.6e-08 vs 3.2e-09) | 0.018 vs 0.15 (0.018 vs 0.15) | 0.0035 vs 0.0045 (0.0035 vs 0.0045) | 1.4e-05 vs 7.4e-10 (1.4e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.0001, cap 20 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | 6.2e-10 vs 3.2e-09 (6.2e-10 vs 3.2e-09) | 0.0003 vs 0.15 (0.0003 vs 0.15) | 0.0002 vs 0.0045 (0.0002 vs 0.0045) | 9e-07 vs 7.4e-10 (9e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.0001, cap 30 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | 4.7e-10 vs 3.2e-09 (4.7e-10 vs 3.2e-09) | 0.0017 vs 0.15 (0.0017 vs 0.15) | 0.00035 vs 0.0045 (0.00035 vs 0.0045) | 6.6e-07 vs 7.4e-10 (6.6e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.0001, cap 40 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | 3.4e-10 vs 3.2e-09 (3.4e-10 vs 3.2e-09) | 0.0033 vs 0.15 (0.0033 vs 0.15) | 0.00047 vs 0.0045 (0.00047 vs 0.0045) | 4.8e-07 vs 7.4e-10 (4.8e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 10 | 0.0029 vs 3.5e-06 (0.0029 vs 3.5e-06) | 1.3e-05 vs 3.2e-09 (1.3e-05 vs 3.2e-09) | 0.048 vs 0.15 (0.048 vs 0.15) | 0.032 vs 0.0045 (0.032 vs 0.0045) | 0.0018 vs 7.4e-10 (0.0018 vs 7.4e-10) | 4.5e-07 vs <1e-12 (4.5e-07 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 20 | 0.00025 vs 3.5e-06 (0.00025 vs 3.5e-06) | 1.9e-05 vs 3.2e-09 (1.9e-05 vs 3.2e-09) | 0.15 vs 0.15 (0.15 vs 0.15) | 0.043 vs 0.0045 (0.043 vs 0.0045) | 0.0015 vs 7.4e-10 (0.0015 vs 7.4e-10) | 2.5e-08 vs <1e-12 (2.5e-08 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 30 | 0.00024 vs 3.5e-06 (0.00024 vs 3.5e-06) | 5.9e-06 vs 3.2e-09 (5.9e-06 vs 3.2e-09) | 0.22 vs 0.15 (0.22 vs 0.15) | 0.049 vs 0.0045 (0.049 vs 0.0045) | 0.0011 vs 7.4e-10 (0.0011 vs 7.4e-10) | 2.5e-08 vs <1e-12 (2.5e-08 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 40 | 2.1e-05 vs 3.5e-06 (2.1e-05 vs 3.5e-06) | 4.9e-06 vs 3.2e-09 (4.9e-06 vs 3.2e-09) | 0.28 vs 0.15 (0.28 vs 0.15) | 0.051 vs 0.0045 (0.051 vs 0.0045) | 0.0007 vs 7.4e-10 (0.0007 vs 7.4e-10) | 1.4e-09 vs <1e-12 (1.4e-09 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 10 | 2.1e-05 vs 3.5e-06 (2.1e-05 vs 3.5e-06) | 3e-06 vs 3.2e-09 (3e-06 vs 3.2e-09) | 0.029 vs 0.15 (0.029 vs 0.15) | 0.012 vs 0.0045 (0.012 vs 0.0045) | 0.00036 vs 7.4e-10 (0.00036 vs 7.4e-10) | 1.4e-09 vs <1e-12 (1.4e-09 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 20 | 2e-05 vs 3.5e-06 (2e-05 vs 3.5e-06) | 1.1e-06 vs 3.2e-09 (1.1e-06 vs 3.2e-09) | 0.073 vs 0.15 (0.073 vs 0.15) | 0.017 vs 0.0045 (0.017 vs 0.0045) | 0.0003 vs 7.4e-10 (0.0003 vs 7.4e-10) | 1.4e-09 vs <1e-12 (1.4e-09 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 30 | 1.7e-06 vs 3.5e-06 (1.7e-06 vs 3.5e-06) | 1.1e-06 vs 3.2e-09 (1.1e-06 vs 3.2e-09) | 0.12 vs 0.15 (0.12 vs 0.15) | 0.02 vs 0.0045 (0.02 vs 0.0045) | 0.00022 vs 7.4e-10 (0.00022 vs 7.4e-10) | 7.8e-11 vs <1e-12 (7.8e-11 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 40 | 1.7e-06 vs 3.5e-06 (1.7e-06 vs 3.5e-06) | 8e-07 vs 3.2e-09 (8e-07 vs 3.2e-09) | 0.16 vs 0.15 (0.16 vs 0.15) | 0.021 vs 0.0045 (0.021 vs 0.0045) | 0.00018 vs 7.4e-10 (0.00018 vs 7.4e-10) | 7.8e-11 vs <1e-12 (7.8e-11 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 10 | 2e-05 vs 3.5e-06 (2e-05 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0053 vs 0.0045 (0.0053 vs 0.0045) | 0.00015 vs 7.4e-10 (0.00015 vs 7.4e-10) | 1.4e-09 vs <1e-12 (1.4e-09 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 20 | 1.7e-06 vs 3.5e-06 (1.7e-06 vs 3.5e-06) | 2.5e-07 vs 3.2e-09 (2.5e-07 vs 3.2e-09) | 0.038 vs 0.15 (0.038 vs 0.15) | 0.0083 vs 0.0045 (0.0083 vs 0.0045) | 0.00011 vs 7.4e-10 (0.00011 vs 7.4e-10) | 7.7e-11 vs <1e-12 (7.7e-11 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 30 | 1.4e-07 vs 3.5e-06 (1.4e-07 vs 3.5e-06) | 1.9e-07 vs 3.2e-09 (1.9e-07 vs 3.2e-09) | 0.077 vs 0.15 (0.077 vs 0.15) | 0.01 vs 0.0045 (0.01 vs 0.0045) | 6.8e-05 vs 7.4e-10 (6.8e-05 vs 7.4e-10) | 4.4e-12 vs <1e-12 (4.4e-12 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 40 | 1.4e-07 vs 3.5e-06 (1.4e-07 vs 3.5e-06) | 6.4e-08 vs 3.2e-09 (6.4e-08 vs 3.2e-09) | 0.1 vs 0.15 (0.1 vs 0.15) | 0.01 vs 0.0045 (0.01 vs 0.0045) | 4.7e-05 vs 7.4e-10 (4.7e-05 vs 7.4e-10) | 4.3e-12 vs <1e-12 (4.3e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 10 | 1.7e-06 vs 3.5e-06 (1.7e-06 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0027 vs 0.0045 (0.0027 vs 0.0045) | 5.2e-05 vs 7.4e-10 (5.2e-05 vs 7.4e-10) | 7.7e-11 vs <1e-12 (7.7e-11 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 20 | 1.4e-07 vs 3.5e-06 (1.4e-07 vs 3.5e-06) | 5.6e-08 vs 3.2e-09 (5.6e-08 vs 3.2e-09) | 0.021 vs 0.15 (0.021 vs 0.15) | 0.0041 vs 0.0045 (0.0041 vs 0.0045) | 3.6e-05 vs 7.4e-10 (3.6e-05 vs 7.4e-10) | 4.3e-12 vs <1e-12 (4.3e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 30 | 1.2e-08 vs 3.5e-06 (1.2e-08 vs 3.5e-06) | 4.3e-08 vs 3.2e-09 (4.3e-08 vs 3.2e-09) | 0.043 vs 0.15 (0.043 vs 0.15) | 0.0049 vs 0.0045 (0.0049 vs 0.0045) | 2.3e-05 vs 7.4e-10 (2.3e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 40 | 1.2e-08 vs 3.5e-06 (1.2e-08 vs 3.5e-06) | 1.5e-08 vs 3.2e-09 (1.5e-08 vs 3.2e-09) | 0.064 vs 0.15 (0.064 vs 0.15) | 0.0052 vs 0.0045 (0.0052 vs 0.0045) | 1.6e-05 vs 7.4e-10 (1.6e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 10 | 1.4e-07 vs 3.5e-06 (1.4e-07 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0014 vs 0.0045 (0.0014 vs 0.0045) | 1.8e-05 vs 7.4e-10 (1.8e-05 vs 7.4e-10) | 4.3e-12 vs <1e-12 (4.3e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 20 | 1.2e-08 vs 3.5e-06 (1.2e-08 vs 3.5e-06) | 1.4e-08 vs 3.2e-09 (1.4e-08 vs 3.2e-09) | 0.017 vs 0.15 (0.017 vs 0.15) | 0.0026 vs 0.0045 (0.0026 vs 0.0045) | 1.4e-05 vs 7.4e-10 (1.4e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 30 | 1e-09 vs 3.5e-06 (1e-09 vs 3.5e-06) | 1e-08 vs 3.2e-09 (1e-08 vs 3.2e-09) | 0.028 vs 0.15 (0.028 vs 0.15) | 0.0026 vs 0.0045 (0.0026 vs 0.0045) | 8.3e-06 vs 7.4e-10 (8.3e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 40 | 9.7e-10 vs 3.5e-06 (9.7e-10 vs 3.5e-06) | 3.6e-09 vs 3.2e-09 (3.6e-09 vs 3.2e-09) | 0.043 vs 0.15 (0.043 vs 0.15) | 0.0031 vs 0.0045 (0.0031 vs 0.0045) | 6.2e-06 vs 7.4e-10 (6.2e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 10 | 1.4e-07 vs 3.5e-06 (1.4e-07 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0014 vs 0.0045 (0.0014 vs 0.0045) | 1.8e-05 vs 7.4e-10 (1.8e-05 vs 7.4e-10) | 4.3e-12 vs <1e-12 (4.3e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 20 | 1.2e-08 vs 3.5e-06 (1.2e-08 vs 3.5e-06) | 9.5e-09 vs 3.2e-09 (9.5e-09 vs 3.2e-09) | 0.0074 vs 0.15 (0.0074 vs 0.15) | 0.0016 vs 0.0045 (0.0016 vs 0.0045) | 1.1e-05 vs 7.4e-10 (1.1e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 30 | 9.7e-10 vs 3.5e-06 (9.7e-10 vs 3.5e-06) | 3.2e-09 vs 3.2e-09 (3.2e-09 vs 3.2e-09) | 0.023 vs 0.15 (0.023 vs 0.15) | 0.002 vs 0.0045 (0.002 vs 0.0045) | 5.2e-06 vs 7.4e-10 (5.2e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 40 | 8.1e-11 vs 3.5e-06 (8.1e-11 vs 3.5e-06) | 8.8e-10 vs 3.2e-09 (8.8e-10 vs 3.2e-09) | 0.03 vs 0.15 (0.03 vs 0.15) | 0.0018 vs 0.0045 (0.0018 vs 0.0045) | 2.3e-06 vs 7.4e-10 (2.3e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 10 | 1.2e-08 vs 3.5e-06 (1.2e-08 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.00069 vs 0.0045 (0.00069 vs 0.0045) | 6.3e-06 vs 7.4e-10 (6.3e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 20 | 8.1e-11 vs 3.5e-06 (8.1e-11 vs 3.5e-06) | 7.2e-10 vs 3.2e-09 (7.2e-10 vs 3.2e-09) | 0.004 vs 0.15 (0.004 vs 0.15) | 0.00058 vs 0.0045 (0.00058 vs 0.0045) | 1.6e-06 vs 7.4e-10 (1.6e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 30 | 8.1e-11 vs 3.5e-06 (8.1e-11 vs 3.5e-06) | 7.5e-10 vs 3.2e-09 (7.5e-10 vs 3.2e-09) | 0.011 vs 0.15 (0.011 vs 0.15) | 0.00095 vs 0.0045 (0.00095 vs 0.0045) | 1.9e-06 vs 7.4e-10 (1.9e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 40 | 8.1e-11 vs 3.5e-06 (8.1e-11 vs 3.5e-06) | 5.4e-10 vs 3.2e-09 (5.4e-10 vs 3.2e-09) | 0.018 vs 0.15 (0.018 vs 0.15) | 0.001 vs 0.0045 (0.001 vs 0.0045) | 1.6e-06 vs 7.4e-10 (1.6e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.0001, cap 20 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | 5.4e-12 vs 3.2e-09 (5.4e-12 vs 3.2e-09) | 0.0003 vs 0.15 (0.0003 vs 0.15) | 7.1e-05 vs 0.0045 (7.1e-05 vs 0.0045) | 1.1e-07 vs 7.4e-10 (1.1e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.0001, cap 30 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | 2.4e-12 vs 3.2e-09 (2.4e-12 vs 3.2e-09) | 0.0017 vs 0.15 (0.0017 vs 0.15) | 9e-05 vs 0.0045 (9e-05 vs 0.0045) | 5.2e-08 vs 7.4e-10 (5.2e-08 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.0001, cap 40 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | 1.6e-12 vs 3.2e-09 (1.6e-12 vs 3.2e-09) | 0.0033 vs 0.15 (0.0033 vs 0.15) | 0.0001 vs 0.0045 (0.0001 vs 0.0045) | 2.8e-08 vs 7.4e-10 (2.8e-08 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 10 | 0.0024 vs 3.5e-06 (0.0024 vs 3.5e-06) | 2.2e-07 vs 3.2e-09 (2.2e-07 vs 3.2e-09) | 0.048 vs 0.15 (0.048 vs 0.15) | 0.024 vs 0.0045 (0.024 vs 0.0045) | 0.00011 vs 7.4e-10 (0.00011 vs 7.4e-10) | 1.8e-11 vs <1e-12 (1.8e-11 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 20 | 0.0002 vs 3.5e-06 (0.0002 vs 3.5e-06) | 2.5e-07 vs 3.2e-09 (2.5e-07 vs 3.2e-09) | 0.15 vs 0.15 (0.15 vs 0.15) | 0.033 vs 0.0045 (0.033 vs 0.0045) | 0.00018 vs 7.4e-10 (0.00018 vs 7.4e-10) | 1.8e-11 vs <1e-12 (1.8e-11 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 30 | 0.0002 vs 3.5e-06 (0.0002 vs 3.5e-06) | 3.7e-08 vs 3.2e-09 (3.7e-08 vs 3.2e-09) | 0.22 vs 0.15 (0.22 vs 0.15) | 0.037 vs 0.0045 (0.037 vs 0.0045) | 8.3e-05 vs 7.4e-10 (8.3e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 40 | 1.7e-05 vs 3.5e-06 (1.7e-05 vs 3.5e-06) | 3.5e-08 vs 3.2e-09 (3.5e-08 vs 3.2e-09) | 0.28 vs 0.15 (0.28 vs 0.15) | 0.037 vs 0.0045 (0.037 vs 0.0045) | 6.8e-05 vs 7.4e-10 (6.8e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 10 | 1.7e-05 vs 3.5e-06 (1.7e-05 vs 3.5e-06) | 3e-08 vs 3.2e-09 (3e-08 vs 3.2e-09) | 0.029 vs 0.15 (0.029 vs 0.15) | 0.0088 vs 0.0045 (0.0088 vs 0.0045) | 3.2e-05 vs 7.4e-10 (3.2e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 20 | 1.6e-05 vs 3.5e-06 (1.6e-05 vs 3.5e-06) | 4.7e-09 vs 3.2e-09 (4.7e-09 vs 3.2e-09) | 0.073 vs 0.15 (0.073 vs 0.15) | 0.012 vs 0.0045 (0.012 vs 0.0045) | 1.8e-05 vs 7.4e-10 (1.8e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 30 | 1.4e-06 vs 3.5e-06 (1.4e-06 vs 3.5e-06) | 4.7e-09 vs 3.2e-09 (4.7e-09 vs 3.2e-09) | 0.12 vs 0.15 (0.12 vs 0.15) | 0.014 vs 0.0045 (0.014 vs 0.0045) | 1.8e-05 vs 7.4e-10 (1.8e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 40 | 1.4e-06 vs 3.5e-06 (1.4e-06 vs 3.5e-06) | 4.1e-09 vs 3.2e-09 (4.1e-09 vs 3.2e-09) | 0.16 vs 0.15 (0.16 vs 0.15) | 0.014 vs 0.0045 (0.014 vs 0.0045) | 1.3e-05 vs 7.4e-10 (1.3e-05 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 10 | 1.6e-05 vs 3.5e-06 (1.6e-05 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0036 vs 0.0045 (0.0036 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 20 | 1.4e-06 vs 3.5e-06 (1.4e-06 vs 3.5e-06) | 6.5e-10 vs 3.2e-09 (6.5e-10 vs 3.2e-09) | 0.038 vs 0.15 (0.038 vs 0.15) | 0.0058 vs 0.0045 (0.0058 vs 0.0045) | 5.2e-06 vs 7.4e-10 (5.2e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 30 | 1.2e-07 vs 3.5e-06 (1.2e-07 vs 3.5e-06) | 5.6e-10 vs 3.2e-09 (5.6e-10 vs 3.2e-09) | 0.077 vs 0.15 (0.077 vs 0.15) | 0.0069 vs 0.0045 (0.0069 vs 0.0045) | 4.1e-06 vs 7.4e-10 (4.1e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 40 | 1.1e-07 vs 3.5e-06 (1.1e-07 vs 3.5e-06) | 8.9e-11 vs 3.2e-09 (8.9e-11 vs 3.2e-09) | 0.1 vs 0.15 (0.1 vs 0.15) | 0.0069 vs 0.0045 (0.0069 vs 0.0045) | 1.9e-06 vs 7.4e-10 (1.9e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 10 | 1.4e-06 vs 3.5e-06 (1.4e-06 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.0018 vs 0.0045 (0.0018 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 20 | 1.1e-07 vs 3.5e-06 (1.1e-07 vs 3.5e-06) | 8.8e-11 vs 3.2e-09 (8.8e-11 vs 3.2e-09) | 0.021 vs 0.15 (0.021 vs 0.15) | 0.0028 vs 0.0045 (0.0028 vs 0.0045) | 1.4e-06 vs 7.4e-10 (1.4e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 30 | 9.9e-09 vs 3.5e-06 (9.9e-09 vs 3.5e-06) | 7.6e-11 vs 3.2e-09 (7.6e-11 vs 3.2e-09) | 0.043 vs 0.15 (0.043 vs 0.15) | 0.0032 vs 0.0045 (0.0032 vs 0.0045) | 1.1e-06 vs 7.4e-10 (1.1e-06 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 40 | 9.5e-09 vs 3.5e-06 (9.5e-09 vs 3.5e-06) | 1.2e-11 vs 3.2e-09 (1.2e-11 vs 3.2e-09) | 0.064 vs 0.15 (0.064 vs 0.15) | 0.0033 vs 0.0045 (0.0033 vs 0.0045) | 5.4e-07 vs 7.4e-10 (5.4e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 10 | 1.1e-07 vs 3.5e-06 (1.1e-07 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.00088 vs 0.0045 (0.00088 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 20 | 9.5e-09 vs 3.5e-06 (9.5e-09 vs 3.5e-06) | 1.2e-11 vs 3.2e-09 (1.2e-11 vs 3.2e-09) | 0.017 vs 0.15 (0.017 vs 0.15) | 0.0017 vs 0.0045 (0.0017 vs 0.0045) | 5e-07 vs 7.4e-10 (5e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 30 | 8.3e-10 vs 3.5e-06 (8.3e-10 vs 3.5e-06) | 1e-11 vs 3.2e-09 (1e-11 vs 3.2e-09) | 0.028 vs 0.15 (0.028 vs 0.15) | 0.0017 vs 0.0045 (0.0017 vs 0.0045) | 3.4e-07 vs 7.4e-10 (3.4e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 40 | 7.9e-10 vs 3.5e-06 (7.9e-10 vs 3.5e-06) | 1.7e-12 vs 3.2e-09 (1.7e-12 vs 3.2e-09) | 0.043 vs 0.15 (0.043 vs 0.15) | 0.0019 vs 0.0045 (0.0019 vs 0.0045) | 1.8e-07 vs 7.4e-10 (1.8e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 10 | 1.1e-07 vs 3.5e-06 (1.1e-07 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.00088 vs 0.0045 (0.00088 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 20 | 9.5e-09 vs 3.5e-06 (9.5e-09 vs 3.5e-06) | 1e-11 vs 3.2e-09 (1e-11 vs 3.2e-09) | 0.0074 vs 0.15 (0.0074 vs 0.15) | 0.001 vs 0.0045 (0.001 vs 0.0045) | 2.8e-07 vs 7.4e-10 (2.8e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 30 | 7.9e-10 vs 3.5e-06 (7.9e-10 vs 3.5e-06) | 1.6e-12 vs 3.2e-09 (1.6e-12 vs 3.2e-09) | 0.023 vs 0.15 (0.023 vs 0.15) | 0.0012 vs 0.0045 (0.0012 vs 0.0045) | 1.4e-07 vs 7.4e-10 (1.4e-07 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 40 | 6.6e-11 vs 3.5e-06 (6.6e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.03 vs 0.15 (0.03 vs 0.15) | 0.0011 vs 0.0045 (0.0011 vs 0.0045) | 5.6e-08 vs 7.4e-10 (5.6e-08 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 10 | 9.4e-09 vs 3.5e-06 (9.4e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | 0.00043 vs 0.0045 (0.00043 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 20 | 6.6e-11 vs 3.5e-06 (6.6e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.004 vs 0.15 (0.004 vs 0.15) | 0.00035 vs 0.0045 (0.00035 vs 0.0045) | 3.7e-08 vs 7.4e-10 (3.7e-08 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 30 | 6.6e-11 vs 3.5e-06 (6.6e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.011 vs 0.15 (0.011 vs 0.15) | 0.00057 vs 0.0045 (0.00057 vs 0.0045) | 4.2e-08 vs 7.4e-10 (4.2e-08 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 40 | 6.6e-11 vs 3.5e-06 (6.6e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.018 vs 0.15 (0.018 vs 0.15) | 0.00059 vs 0.0045 (0.00059 vs 0.0045) | 2.9e-08 vs 7.4e-10 (2.9e-08 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.0001, cap 20 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0003 vs 0.15 (0.0003 vs 0.15) | 4e-05 vs 0.0045 (4e-05 vs 0.0045) | 5e-10 vs 7.4e-10 (5e-10 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.0001, cap 30 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0017 vs 0.15 (0.0017 vs 0.15) | 4.9e-05 vs 0.0045 (4.9e-05 vs 0.0045) | 3.6e-10 vs 7.4e-10 (3.6e-10 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.0001, cap 40 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0033 vs 0.15 (0.0033 vs 0.15) | 5.2e-05 vs 0.0045 (5.2e-05 vs 0.0045) | 2.5e-10 vs 7.4e-10 (2.5e-10 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 10 | 0.0014 vs 3.5e-06 (0.0014 vs 3.5e-06) | 4.2e-08 vs 3.2e-09 (4.2e-08 vs 3.2e-09) | 0.036 vs 0.15 (0.036 vs 0.15) | 0.0015 vs 0.0045 (0.0015 vs 0.0045) | 4.9e-08 vs 7.4e-10 (4.9e-08 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 20 | 0.00012 vs 3.5e-06 (0.00012 vs 3.5e-06) | 4.5e-08 vs 3.2e-09 (4.5e-08 vs 3.2e-09) | 0.11 vs 0.15 (0.11 vs 0.15) | 0.0035 vs 0.0045 (0.0035 vs 0.0045) | 5.3e-08 vs 7.4e-10 (5.3e-08 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 30 | 0.00012 vs 3.5e-06 (0.00012 vs 3.5e-06) | 5.1e-09 vs 3.2e-09 (5.1e-09 vs 3.2e-09) | 0.16 vs 0.15 (0.16 vs 0.15) | 0.0028 vs 0.0045 (0.0028 vs 0.0045) | 6.3e-09 vs 7.4e-10 (6.3e-09 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 40 | 1e-05 vs 3.5e-06 (1e-05 vs 3.5e-06) | 4.9e-09 vs 3.2e-09 (4.9e-09 vs 3.2e-09) | 0.2 vs 0.15 (0.2 vs 0.15) | 0.0026 vs 0.0045 (0.0026 vs 0.0045) | 6e-09 vs 7.4e-10 (6e-09 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 10 | 1e-05 vs 3.5e-06 (1e-05 vs 3.5e-06) | 4.5e-09 vs 3.2e-09 (4.5e-09 vs 3.2e-09) | 0.021 vs 0.15 (0.021 vs 0.15) | 0.00061 vs 0.0045 (0.00061 vs 0.0045) | 5.4e-09 vs 7.4e-10 (5.4e-09 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 20 | 1e-05 vs 3.5e-06 (1e-05 vs 3.5e-06) | 5.4e-10 vs 3.2e-09 (5.4e-10 vs 3.2e-09) | 0.049 vs 0.15 (0.049 vs 0.15) | 0.00068 vs 0.0045 (0.00068 vs 0.0045) | 6.7e-10 vs 7.4e-10 (6.7e-10 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 30 | 8.7e-07 vs 3.5e-06 (8.7e-07 vs 3.5e-06) | 5.4e-10 vs 3.2e-09 (5.4e-10 vs 3.2e-09) | 0.078 vs 0.15 (0.078 vs 0.15) | 0.00081 vs 0.0045 (0.00081 vs 0.0045) | 6.7e-10 vs 7.4e-10 (6.7e-10 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 40 | 8.7e-07 vs 3.5e-06 (8.7e-07 vs 3.5e-06) | 4.9e-10 vs 3.2e-09 (4.9e-10 vs 3.2e-09) | 0.1 vs 0.15 (0.1 vs 0.15) | 0.00063 vs 0.0045 (0.00063 vs 0.0045) | 6.1e-10 vs 7.4e-10 (6.1e-10 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 10 | 1e-05 vs 3.5e-06 (1e-05 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 20 | 8.4e-07 vs 3.5e-06 (8.4e-07 vs 3.5e-06) | 5.9e-11 vs 3.2e-09 (5.9e-11 vs 3.2e-09) | 0.025 vs 0.15 (0.025 vs 0.15) | 0.00026 vs 0.0045 (0.00026 vs 0.0045) | 7.5e-11 vs 7.4e-10 (7.5e-11 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 30 | 7.3e-08 vs 3.5e-06 (7.3e-08 vs 3.5e-06) | 5.3e-11 vs 3.2e-09 (5.3e-11 vs 3.2e-09) | 0.048 vs 0.15 (0.048 vs 0.15) | 0.00028 vs 0.0045 (0.00028 vs 0.0045) | 6.8e-11 vs 7.4e-10 (6.8e-11 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 40 | 7e-08 vs 3.5e-06 (7e-08 vs 3.5e-06) | 6.4e-12 vs 3.2e-09 (6.4e-12 vs 3.2e-09) | 0.06 vs 0.15 (0.06 vs 0.15) | 0.0002 vs 0.0045 (0.0002 vs 0.0045) | 8.5e-12 vs 7.4e-10 (8.5e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 10 | 8.4e-07 vs 3.5e-06 (8.4e-07 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 20 | 7e-08 vs 3.5e-06 (7e-08 vs 3.5e-06) | 6.4e-12 vs 3.2e-09 (6.4e-12 vs 3.2e-09) | 0.013 vs 0.15 (0.013 vs 0.15) | 9.3e-05 vs 0.0045 (9.3e-05 vs 0.0045) | 8.4e-12 vs 7.4e-10 (8.4e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 30 | 6.1e-09 vs 3.5e-06 (6.1e-09 vs 3.5e-06) | 5.8e-12 vs 3.2e-09 (5.8e-12 vs 3.2e-09) | 0.025 vs 0.15 (0.025 vs 0.15) | 9.8e-05 vs 0.0045 (9.8e-05 vs 0.0045) | 7.6e-12 vs 7.4e-10 (7.6e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 40 | 5.8e-09 vs 3.5e-06 (5.8e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.036 vs 0.15 (0.036 vs 0.15) | 7.4e-05 vs 0.0045 (7.4e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 10 | 7e-08 vs 3.5e-06 (7e-08 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 20 | 5.8e-09 vs 3.5e-06 (5.8e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.01 vs 0.15 (0.01 vs 0.15) | 4.8e-05 vs 0.0045 (4.8e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 30 | 5.1e-10 vs 3.5e-06 (5.1e-10 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.015 vs 0.15 (0.015 vs 0.15) | 4e-05 vs 0.0045 (4e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 40 | 4.9e-10 vs 3.5e-06 (4.9e-10 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.023 vs 0.15 (0.023 vs 0.15) | 3.5e-05 vs 0.0045 (3.5e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 10 | 7e-08 vs 3.5e-06 (7e-08 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 20 | 5.8e-09 vs 3.5e-06 (5.8e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0044 vs 0.15 (0.0044 vs 0.15) | 2.3e-05 vs 0.0045 (2.3e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 30 | 4.9e-10 vs 3.5e-06 (4.9e-10 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.012 vs 0.15 (0.012 vs 0.15) | 2.3e-05 vs 0.0045 (2.3e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 40 | 4.1e-11 vs 3.5e-06 (4.1e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.015 vs 0.15 (0.015 vs 0.15) | 1.6e-05 vs 0.0045 (1.6e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 10 | 5.8e-09 vs 3.5e-06 (5.8e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 20 | 4.1e-11 vs 3.5e-06 (4.1e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0022 vs 0.15 (0.0022 vs 0.15) | 5.9e-06 vs 0.0045 (5.9e-06 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 30 | 4.1e-11 vs 3.5e-06 (4.1e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.006 vs 0.15 (0.006 vs 0.15) | 9e-06 vs 0.0045 (9e-06 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 40 | 4.1e-11 vs 3.5e-06 (4.1e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0087 vs 0.15 (0.0087 vs 0.15) | 7e-06 vs 0.0045 (7e-06 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.0001, cap 20 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.00015 vs 0.15 (0.00015 vs 0.15) | 1.6e-07 vs 0.0045 (1.6e-07 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.0001, cap 30 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.00075 vs 0.15 (0.00075 vs 0.15) | 2.7e-07 vs 0.0045 (2.7e-07 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.0001, cap 40 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0014 vs 0.15 (0.0014 vs 0.15) | 2.5e-07 vs 0.0045 (2.5e-07 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 10 | 0.00054 vs 3.5e-06 (0.00054 vs 3.5e-06) | 6.6e-10 vs 3.2e-09 (6.6e-10 vs 3.2e-09) | 0.036 vs 0.15 (0.036 vs 0.15) | 0.00088 vs 0.0045 (0.00088 vs 0.0045) | 1.5e-10 vs 7.4e-10 (1.5e-10 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 20 | 4.6e-05 vs 3.5e-06 (4.6e-05 vs 3.5e-06) | 6.8e-10 vs 3.2e-09 (6.8e-10 vs 3.2e-09) | 0.11 vs 0.15 (0.11 vs 0.15) | 0.0018 vs 0.0045 (0.0018 vs 0.0045) | 1.6e-10 vs 7.4e-10 (1.6e-10 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 30 | 4.5e-05 vs 3.5e-06 (4.5e-05 vs 3.5e-06) | 4.7e-11 vs 3.2e-09 (4.7e-11 vs 3.2e-09) | 0.16 vs 0.15 (0.16 vs 0.15) | 0.0013 vs 0.0045 (0.0013 vs 0.0045) | 8.8e-12 vs 7.4e-10 (8.8e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 40 | 3.9e-06 vs 3.5e-06 (3.9e-06 vs 3.5e-06) | 4.6e-11 vs 3.2e-09 (4.6e-11 vs 3.2e-09) | 0.2 vs 0.15 (0.2 vs 0.15) | 0.0011 vs 0.0045 (0.0011 vs 0.0045) | 8.7e-12 vs 7.4e-10 (8.7e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 10 | 3.9e-06 vs 3.5e-06 (3.9e-06 vs 3.5e-06) | 4.5e-11 vs 3.2e-09 (4.5e-11 vs 3.2e-09) | 0.021 vs 0.15 (0.021 vs 0.15) | 0.00033 vs 0.0045 (0.00033 vs 0.0045) | 8.5e-12 vs 7.4e-10 (8.5e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 20 | 3.8e-06 vs 3.5e-06 (3.8e-06 vs 3.5e-06) | 3.1e-12 vs 3.2e-09 (3.1e-12 vs 3.2e-09) | 0.049 vs 0.15 (0.049 vs 0.15) | 0.00031 vs 0.0045 (0.00031 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 30 | 3.3e-07 vs 3.5e-06 (3.3e-07 vs 3.5e-06) | 3.1e-12 vs 3.2e-09 (3.1e-12 vs 3.2e-09) | 0.078 vs 0.15 (0.078 vs 0.15) | 0.00035 vs 0.0045 (0.00035 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 40 | 3.2e-07 vs 3.5e-06 (3.2e-07 vs 3.5e-06) | 3e-12 vs 3.2e-09 (3e-12 vs 3.2e-09) | 0.1 vs 0.15 (0.1 vs 0.15) | 0.00026 vs 0.0045 (0.00026 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 10 | 3.8e-06 vs 3.5e-06 (3.8e-06 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 20 | 3.1e-07 vs 3.5e-06 (3.1e-07 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.025 vs 0.15 (0.025 vs 0.15) | 0.00011 vs 0.0045 (0.00011 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 30 | 2.7e-08 vs 3.5e-06 (2.7e-08 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.048 vs 0.15 (0.048 vs 0.15) | 0.00011 vs 0.0045 (0.00011 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 40 | 2.6e-08 vs 3.5e-06 (2.6e-08 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.06 vs 0.15 (0.06 vs 0.15) | 7.1e-05 vs 0.0045 (7.1e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 10 | 3.1e-07 vs 3.5e-06 (3.1e-07 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 20 | 2.6e-08 vs 3.5e-06 (2.6e-08 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.013 vs 0.15 (0.013 vs 0.15) | 3.8e-05 vs 0.0045 (3.8e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 30 | 2.3e-09 vs 3.5e-06 (2.3e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.025 vs 0.15 (0.025 vs 0.15) | 3.6e-05 vs 0.0045 (3.6e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 40 | 2.2e-09 vs 3.5e-06 (2.2e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.036 vs 0.15 (0.036 vs 0.15) | 2.5e-05 vs 0.0045 (2.5e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 10 | 2.6e-08 vs 3.5e-06 (2.6e-08 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 20 | 2.2e-09 vs 3.5e-06 (2.2e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.01 vs 0.15 (0.01 vs 0.15) | 1.8e-05 vs 0.0045 (1.8e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 30 | 1.9e-10 vs 3.5e-06 (1.9e-10 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.015 vs 0.15 (0.015 vs 0.15) | 1.4e-05 vs 0.0045 (1.4e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 40 | 1.8e-10 vs 3.5e-06 (1.8e-10 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.023 vs 0.15 (0.023 vs 0.15) | 1.1e-05 vs 0.0045 (1.1e-05 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 10 | 2.6e-08 vs 3.5e-06 (2.6e-08 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 20 | 2.2e-09 vs 3.5e-06 (2.2e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0044 vs 0.15 (0.0044 vs 0.15) | 8.9e-06 vs 0.0045 (8.9e-06 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 30 | 1.8e-10 vs 3.5e-06 (1.8e-10 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.012 vs 0.15 (0.012 vs 0.15) | 7.5e-06 vs 0.0045 (7.5e-06 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 40 | 1.5e-11 vs 3.5e-06 (1.5e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.015 vs 0.15 (0.015 vs 0.15) | 4.5e-06 vs 0.0045 (4.5e-06 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 10 | 2.2e-09 vs 3.5e-06 (2.2e-09 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | <1e-12 vs 0.15 (<1e-12 vs 0.15) | <1e-12 vs 0.0045 (<1e-12 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 20 | 1.5e-11 vs 3.5e-06 (1.5e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0022 vs 0.15 (0.0022 vs 0.15) | 2e-06 vs 0.0045 (2e-06 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 30 | 1.5e-11 vs 3.5e-06 (1.5e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.006 vs 0.15 (0.006 vs 0.15) | 2.8e-06 vs 0.0045 (2.8e-06 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 40 | 1.5e-11 vs 3.5e-06 (1.5e-11 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0087 vs 0.15 (0.0087 vs 0.15) | 2e-06 vs 0.0045 (2e-06 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.0001, cap 20 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.00015 vs 0.15 (0.00015 vs 0.15) | 4.6e-08 vs 0.0045 (4.6e-08 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.0001, cap 30 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.00075 vs 0.15 (0.00075 vs 0.15) | 6.4e-08 vs 0.0045 (6.4e-08 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.0001, cap 40 | <1e-12 vs 3.5e-06 (<1e-12 vs 3.5e-06) | <1e-12 vs 3.2e-09 (<1e-12 vs 3.2e-09) | 0.0014 vs 0.15 (0.0014 vs 0.15) | 5.4e-08 vs 0.0045 (5.4e-08 vs 0.0045) | <1e-12 vs 7.4e-10 (<1e-12 vs 7.4e-10) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |

Per group, the current rule against delta 0.02, alpha 0.01, cap 20, delta 0.03, alpha 0.003, cap 20: the false-switch rate at gain 0 (m equal challengers; in brackets, with the group's contest effect added), and the power at 5% and 10%:

| group | current: rate (contest effect) | 5% | 10% | d 0.02 a 0.01 c 20: rate (contest effect) | 5% | 10% | d 0.03 a 0.003 c 20: rate (contest effect) | 5% | 10% |
|---|---|---|---|---|---|---|---|---|---|
| dev2-before | 3.5e-06 (3.5e-06) | 0.000 | 0.013 | 2e-06 (2e-06) | 0.000 | 0.183 | 9.5e-09 (9.5e-09) | 0.000 | 0.007 |
| dev2-after | 3.2e-09 (3.2e-09) | 0.424 | 0.980 | 5.9e-06 (5.9e-06) | 0.900 | 0.999 | 1.2e-11 (1.2e-11) | 0.817 | 0.993 |
| dev3-before | 0.15 (0.15) | 0.286 | 0.407 | 0.038 (0.038) | 0.092 | 0.180 | 0.017 (0.017) | 0.049 | 0.113 |
| dev3-after | 0.0045 (0.0045) | 0.193 | 0.728 | 0.017 (0.017) | 0.383 | 0.775 | 0.0017 (0.0017) | 0.133 | 0.508 |
| dev4-before | 7.4e-10 (7.4e-10) | 0.244 | 1.000 | 0.00046 (0.00046) | 0.987 | 1.000 | 5e-07 (5e-07) | 0.960 | 1.000 |
| dev4-after | <1e-12 (<1e-12) | 0.011 | 0.991 | 7.7e-11 (7.7e-11) | 0.925 | 1.000 | <1e-12 (<1e-12) | 0.598 | 1.000 |

## The null

### dev2-before: 96 rounds, 24 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.3107 | 0.1725 | -0.0966 | -1.414 | -1.008 | -0.446 | +0.511 | +0.609 | +0.714 | 0.417 (40) [0.317, 0.522] | 0.677 |

- Load (1-min) 1.7-3.1, median 2.0; the preference's time per round 0.0011-0.00451 s, median 0.00116.
- Order: mean x -0.0436 with the A/A arm after the preference (48 rounds), -0.1496 before it (48).
- Successive rounds: lag-1 correlation -0.234; contest means vary 0.40x what independent rounds give (24 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.3362 (24), n=4096 0.3088 (24).
- Distinct challengers per round (most common): 1.

### dev2-after: 74 rounds, 24 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.1548 | 0.0180 | -0.0260 | -1.216 | -0.513 | -0.069 | +0.060 | +0.088 | +0.093 | 0.0676 (5) [0.0223, 0.151] | 0.703 |

- Load (1-min) 0.9-1.9, median 1.7; the preference's time per round 9.8e-04-0.00371 s, median 0.00105.
- Order: mean x -0.0423 with the A/A arm after the preference (48 rounds), +0.0041 before it (26).
- Successive rounds: lag-1 correlation -0.075; contest means vary 0.73x what independent rounds give (24 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.1415 (24), n=4096 0.1381 (24).
- Distinct challengers per round (most common): 1.

### dev3-before: 83 rounds, 24 contests (gravity-dev3)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.2375 | 0.2176 | -0.0348 | -0.442 | -0.366 | -0.316 | +0.358 | +0.405 | +0.435 | 0.578 (48) [0.465, 0.686] | 0.651 |

- Load (1-min) 0.7-1.8, median 1.1; the preference's time per round 0.00771-0.013 s, median 0.0104.
- Order: mean x -0.2100 with the A/A arm after the preference (48 rounds), +0.2056 before it (35).
- Successive rounds: lag-1 correlation -0.773; contest means vary 0.08x what independent rounds give (24 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.2813 (24), n=4096 0.1287 (24).
- Distinct challengers per round (most common): 1.

### dev3-after: 75 rounds, 24 contests (gravity-dev3)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0973 | 0.0928 | -0.0276 | -0.249 | -0.247 | -0.178 | +0.133 | +0.154 | +0.156 | 0.373 (28) [0.264, 0.493] | 0.613 |

- Load (1-min) 0.7-2.0, median 1.0; the preference's time per round 0.0078-0.0118 s, median 0.00876.
- Order: mean x -0.0273 with the A/A arm after the preference (48 rounds), -0.0282 before it (27).
- Successive rounds: lag-1 correlation 0.260; contest means vary 0.37x what independent rounds give (24 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.1069 (24), n=4096 0.0868 (24).
- Distinct challengers per round (most common): 1.

### dev4-before: 72 rounds, 24 contests (gravity-dev4)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0243 | 0.0252 | -0.0141 | -0.070 | -0.064 | -0.053 | +0.026 | +0.042 | +0.043 | 0.0556 (4) [0.0153, 0.136] | 0.639 |

- Load (1-min) 0.4-0.6, median 0.5; the preference's time per round 0.0105-0.0116 s, median 0.0112.
- Order: mean x -0.0123 with the A/A arm after the preference (48 rounds), -0.0177 before it (24).
- Successive rounds: lag-1 correlation 0.044; contest means vary 0.72x what independent rounds give (24 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0255 (24), n=4096 0.0358 (24).
- Distinct challengers per round (most common): 1.

### dev4-after: 72 rounds, 24 contests (gravity-dev4)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0223 | 0.0154 | +0.0059 | -0.056 | -0.044 | -0.023 | +0.049 | +0.070 | +0.072 | 0.0139 (1) [3.5e-04, 0.075] | 0.403 |

- Load (1-min) 0.2-0.8, median 0.5; the preference's time per round 0.00999-0.0116 s, median 0.0105.
- Order: mean x +0.0009 with the A/A arm after the preference (48 rounds), +0.0158 before it (24).
- Successive rounds: lag-1 correlation -0.055; contest means vary 0.89x what independent rounds give (24 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0227 (24), n=4096 0.0214 (24).
- Distinct challengers per round (most common): 1.

## Dependence on load, work and place in the contest

### dev2-before

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 1.71-1.81 | 16 | 0.4602 | 0.1723 | 0.438 |
| load (1-min) | 1.81-1.9 | 20 | 0.2765 | 0.1903 | 0.45 |
| load (1-min) | 1.9-2.08 | 20 | 0.3040 | 0.1658 | 0.5 |
| load (1-min) | 2.08-2.79 | 20 | 0.2518 | 0.1603 | 0.35 |
| load (1-min) | 2.79-3.14 | 20 | 0.2561 | 0.1363 | 0.35 |
| preference's time (s) | 0.0011-0.00112 | 19 | 0.0333 | 0.0143 | 0.0526 |
| preference's time (s) | 0.00112-0.00114 | 19 | 0.1498 | 0.0130 | 0.316 |
| preference's time (s) | 0.00114-0.00118 | 19 | 0.1870 | 0.0379 | 0 |
| preference's time (s) | 0.00118-0.00156 | 19 | 0.3438 | 0.1758 | 0.684 |
| preference's time (s) | 0.00156-0.00451 | 20 | 0.2762 | 0.0399 | 1 |
| timed runs in the round | 2.5-3.5 | 96 | 0.3107 | 0.1725 | 0.417 |
| round of the contest | 1-2 | 24 | 0.0426 | 0.0245 | 0.208 |
| round of the contest | 2-4 | 48 | 0.3485 | 0.1409 | 0.688 |
| round of the contest | 4-6 | 24 | 0.3026 | 0.0379 | 0.0833 |

### dev2-after

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.889-1.38 | 15 | 0.0279 | 0.0147 | 0 |
| load (1-min) | 1.38-1.64 | 15 | 0.0277 | 0.0108 | 0 |
| load (1-min) | 1.64-1.71 | 13 | 0.0620 | 0.0273 | 0.154 |
| load (1-min) | 1.71-1.87 | 15 | 0.0346 | 0.0113 | 0 |
| load (1-min) | 1.87-1.94 | 16 | 0.3248 | 0.0275 | 0.188 |
| preference's time (s) | 9.8e-04-0.001 | 15 | 0.0127 | 0.0054 | 0 |
| preference's time (s) | 0.001-0.00104 | 15 | 0.0289 | 0.0124 | 0 |
| preference's time (s) | 0.00104-0.00106 | 14 | 0.0401 | 0.0053 | 0 |
| preference's time (s) | 0.00106-0.00107 | 15 | 0.0244 | 0.0093 | 0 |
| preference's time (s) | 0.00107-0.00371 | 15 | 0.3294 | 0.0434 | 0.333 |
| timed runs in the round | 2.5-3.5 | 74 | 0.1548 | 0.0180 | 0.0676 |
| round of the contest | 1-2 | 24 | 0.0335 | 0.0147 | 0.0417 |
| round of the contest | 2-4 | 48 | 0.1900 | 0.0189 | 0.0833 |

### dev3-before

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.718-0.892 | 16 | 0.2259 | 0.2001 | 0.562 |
| load (1-min) | 0.892-1.06 | 17 | 0.2650 | 0.1796 | 0.529 |
| load (1-min) | 1.06-1.11 | 17 | 0.2484 | 0.1840 | 0.588 |
| load (1-min) | 1.11-1.27 | 14 | 0.2337 | 0.1777 | 0.571 |
| load (1-min) | 1.27-1.77 | 19 | 0.2363 | 0.2555 | 0.632 |
| preference's time (s) | 0.00771-0.00859 | 17 | 0.0568 | 0.0563 | 0 |
| preference's time (s) | 0.00859-0.00986 | 16 | 0.1499 | 0.0834 | 0.0625 |
| preference's time (s) | 0.00986-0.0107 | 17 | 0.1138 | 0.0975 | 0.882 |
| preference's time (s) | 0.0107-0.0118 | 16 | 0.0868 | 0.1019 | 1 |
| preference's time (s) | 0.0118-0.013 | 17 | 0.1080 | 0.0920 | 0.941 |
| timed runs in the round | 2.5-3.5 | 83 | 0.2375 | 0.2176 | 0.578 |
| round of the contest | 1-2 | 24 | 0.0673 | 0.0696 | 0.958 |
| round of the contest | 2-4 | 48 | 0.2893 | 0.4241 | 0.5 |
| round of the contest | 4-6 | 11 | 0.0523 | 0.0438 | 0.0909 |

### dev3-after

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.667-0.873 | 14 | 0.1191 | 0.1211 | 0.429 |
| load (1-min) | 0.873-0.962 | 14 | 0.0913 | 0.0923 | 0.357 |
| load (1-min) | 0.962-1.11 | 16 | 0.0949 | 0.0862 | 0.375 |
| load (1-min) | 1.11-1.33 | 16 | 0.1023 | 0.1019 | 0.375 |
| load (1-min) | 1.33-2.01 | 15 | 0.0885 | 0.0657 | 0.333 |
| preference's time (s) | 0.0078-0.00817 | 15 | 0.0599 | 0.0570 | 0.0667 |
| preference's time (s) | 0.00817-0.00858 | 15 | 0.0405 | 0.0282 | 0.0667 |
| preference's time (s) | 0.00858-0.00897 | 15 | 0.0494 | 0.0409 | 0.4 |
| preference's time (s) | 0.00897-0.0101 | 15 | 0.0659 | 0.0503 | 0.333 |
| preference's time (s) | 0.0101-0.0118 | 15 | 0.0439 | 0.0228 | 1 |
| timed runs in the round | 2.5-3.5 | 75 | 0.0973 | 0.0928 | 0.373 |
| round of the contest | 1-2 | 24 | 0.0737 | 0.0787 | 0.708 |
| round of the contest | 2-4 | 48 | 0.0795 | 0.0909 | 0.229 |

### dev4-before

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.427-0.459 | 13 | 0.0292 | 0.0363 | 0.0769 |
| load (1-min) | 0.459-0.506 | 14 | 0.0218 | 0.0253 | 0 |
| load (1-min) | 0.506-0.546 | 16 | 0.0267 | 0.0274 | 0.0625 |
| load (1-min) | 0.546-0.584 | 14 | 0.0269 | 0.0233 | 0.0714 |
| load (1-min) | 0.584-0.649 | 15 | 0.0194 | 0.0166 | 0.0667 |
| preference's time (s) | 0.0105-0.0108 | 15 | 0.0256 | 0.0237 | 0 |
| preference's time (s) | 0.0108-0.0111 | 14 | 0.0213 | 0.0139 | 0 |
| preference's time (s) | 0.0111-0.0112 | 14 | 0.0196 | 0.0233 | 0.0714 |
| preference's time (s) | 0.0112-0.0113 | 14 | 0.0179 | 0.0167 | 0 |
| preference's time (s) | 0.0113-0.0116 | 15 | 0.0286 | 0.0152 | 0.2 |
| timed runs in the round | 2.5-3.5 | 72 | 0.0243 | 0.0252 | 0.0556 |
| round of the contest | 1-2 | 24 | 0.0106 | 0.0065 | 0 |
| round of the contest | 2-4 | 48 | 0.0253 | 0.0185 | 0.0833 |

### dev4-after

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.181-0.464 | 13 | 0.0324 | 0.0328 | 0.0769 |
| load (1-min) | 0.464-0.483 | 14 | 0.0098 | 0.0093 | 0 |
| load (1-min) | 0.483-0.573 | 15 | 0.0209 | 0.0135 | 0 |
| load (1-min) | 0.573-0.611 | 13 | 0.0169 | 0.0108 | 0 |
| load (1-min) | 0.611-0.792 | 17 | 0.0272 | 0.0136 | 0 |
| preference's time (s) | 0.00999-0.0104 | 15 | 0.0168 | 0.0090 | 0 |
| preference's time (s) | 0.0104-0.0105 | 14 | 0.0252 | 0.0116 | 0 |
| preference's time (s) | 0.0105-0.0106 | 14 | 0.0256 | 0.0259 | 0 |
| preference's time (s) | 0.0106-0.0112 | 14 | 0.0237 | 0.0098 | 0.0714 |
| preference's time (s) | 0.0112-0.0116 | 15 | 0.0128 | 0.0082 | 0 |
| timed runs in the round | 2.5-3.5 | 72 | 0.0223 | 0.0154 | 0.0139 |
| round of the contest | 1-2 | 24 | 0.0131 | 0.0096 | 0 |
| round of the contest | 2-4 | 48 | 0.0252 | 0.0154 | 0.0208 |

## The current rule's false-switch rate (TIE 5%, 75% share, minimum 5, cap 10)

The first contest draws rounds 1-3 from their own samples and later rounds by parity; the confirmation, a contest that starts later, draws every round from the later rounds (contest rounds after the third, and confirmation rounds), by parity. The last but one column draws the confirmation from the logged confirmation rounds alone (pooled; with the range its 95% interval gives), where at least 20 were logged.

| group | P(round win) [95% CI] | rounds 1 / 2 / 3, later odd / even | contest, m=1 | confirmed, m=1 | confirmed, m | m | confirmed, m, every sample at its 95% CI's upper end | with the contest effect (tau) | confirmed, m, from the logged confirmations [95% CI] (rounds) | rounds (equal arms) |
|---|---|---|---|---|---|---|---|---|---|---|
| dev2-before | 0.417 [0.317, 0.522] | 0.208 / 1.000 / 0.375 / 0.083 / 0.083 | 0.016 | 3.5e-06 | 3.5e-06 | 1 | 0.0037 | 3.5e-06 (0.000) | - | 4.69 |
| dev2-after | 0.0676 [0.0223, 0.151] | 0.042 / 0.000 / 0.167 / 0.068 / 0.068 | 3.2e-05 | 3.2e-09 | 3.2e-09 | 1 | 1.5e-05 | 3.2e-09 (0.000) | - | 3.22 |
| dev3-before | 0.578 [0.465, 0.686] | 0.958 / 0.000 / 1.000 / 0.578 / 0.578 | 0.41 | 0.15 | 0.15 | 1 | 0.39 | 0.15 (0.000) | - | 5.90 |
| dev3-after | 0.373 [0.264, 0.493] | 0.708 / 0.458 / 0.000 / 0.373 / 0.373 | 0.057 | 0.0045 | 0.0045 | 1 | 0.052 | 0.0045 (0.000) | - | 4.70 |
| dev4-before | 0.0556 [0.0153, 0.136] | 0.000 / 0.125 / 0.042 / 0.056 / 0.056 | 1.6e-05 | 7.4e-10 | 7.4e-10 | 1 | 7.5e-06 | 7.4e-10 (0.000) | - | 3.18 |
| dev4-after | 0.0139 [3.5e-04, 0.075] | 0.000 / 0.042 / 0.000 / 0.014 / 0.014 | 2.2e-11 | <1e-12 | <1e-12 | 1 | 1.5e-07 | <1e-12 (0.000) | - | 3.04 |

On the logged A/A sequences in their order (contests of at least 10 or 20 rounds, cut into windows from round 1, so a contest's first window holds its first rounds), against the switches the model expects at each window's place:

| group | window | rule | windows | switches | expected (model) |
|---|---|---|---|---|---|

## Rules under the dev2-before null (96 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 3.5e-06 | 3.5e-06 | 0.000 | 0.000 | 0.013 | 4.7 | 5.7 |
| 20 | 3.5e-06 | 3.5e-06 | 0.000 | 0.000 | 0.013 | 7.0 | 8.1 |
| 30 | 3.5e-06 | 3.5e-06 | 0.000 | 0.000 | 0.013 | 7.5 | 9.6 |
| 40 | 3.5e-06 | 3.5e-06 | 0.000 | 0.000 | 0.013 | 8.0 | 11.7 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00015 | 0.00015 | 0.000 | 0.003 | 0.327 | 3.5 | 4.0 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 1.9e-05 | 1.9e-05 | 0.000 | 0.001 | 0.642 | 7.1 | 8.1 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 2.5e-06 | 2.5e-06 | 0.000 | 0.000 | 0.849 | 11.7 | 13.4 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 2.4e-06 | 2.4e-06 | 0.000 | 0.000 | 0.924 | 15.1 | 17.4 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 2.9e-07 | 2.9e-07 | 0.000 | 0.000 | 0.162 | 3.5 | 4.0 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 4.6e-09 | 4.6e-09 | 0.000 | 0.000 | 0.317 | 6.0 | 6.7 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 4.6e-09 | 4.6e-09 | 0.000 | 0.000 | 0.561 | 9.4 | 10.7 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 4.6e-09 | 4.6e-09 | 0.000 | 0.000 | 0.726 | 12.8 | 14.7 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 7.1e-11 | 7.1e-11 | 0.000 | 0.000 | 0.125 | 4.8 | 5.4 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 8.9e-12 | 8.9e-12 | 0.000 | 0.000 | 0.320 | 8.2 | 9.4 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 1.1e-12 | 1.1e-12 | 0.000 | 0.000 | 0.506 | 11.7 | 13.4 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 2.4e-05 | 2.4e-05 | 0.000 | 0.000 | 0.127 | 3.1 | 3.7 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 2e-06 | 2e-06 | 0.000 | 0.000 | 0.183 | 6.7 | 7.2 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 1.7e-07 | 1.7e-07 | 0.000 | 0.000 | 0.239 | 11.1 | 11.8 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 1.7e-07 | 1.7e-07 | 0.000 | 0.000 | 0.276 | 14.4 | 15.2 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 1.4e-08 | 1.4e-08 | 0.000 | 0.000 | 0.031 | 3.1 | 3.7 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 9.6e-11 | 9.6e-11 | 0.000 | 0.000 | 0.035 | 5.6 | 6.1 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 9.6e-11 | 9.6e-11 | 0.000 | 0.000 | 0.061 | 8.9 | 9.5 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 9.6e-11 | 9.6e-11 | 0.000 | 0.000 | 0.079 | 12.2 | 13.0 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.008 | 4.5 | 5.0 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.014 | 7.8 | 8.4 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.020 | 11.1 | 11.8 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 3.8e-06 | 3.8e-06 | 0.000 | 0.000 | 0.006 | 1.5 | 3.5 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 3.1e-07 | 3.1e-07 | 0.000 | 0.000 | 0.002 | 5.8 | 7.1 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 2.7e-08 | 2.7e-08 | 0.000 | 0.000 | 0.001 | 10.2 | 11.7 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 2.6e-08 | 2.6e-08 | 0.000 | 0.000 | 0.001 | 13.5 | 15.1 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 2.2e-09 | 2.2e-09 | 0.000 | 0.000 | 0.000 | 1.5 | 3.5 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 1.5e-11 | 1.5e-11 | 0.000 | 0.000 | 0.000 | 4.7 | 6.0 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 1.5e-11 | 1.5e-11 | 0.000 | 0.000 | 0.000 | 8.0 | 9.4 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 1.5e-11 | 1.5e-11 | 0.000 | 0.000 | 0.000 | 11.3 | 12.8 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.000 | 3.6 | 4.8 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.000 | 6.9 | 8.2 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.2 | 11.7 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 20000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00315 | 0.01 | 0.022 | 0.047 | 0.365 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00165 | 0.0091 | 0.017 | 0.048 | 0.376 | 19.9 |
| t | 0 | 0.01 | 30 | 0.00125 | 0.01 | 0.019 | 0.071 | 0.451 | 29.8 |
| t | 0 | 0.01 | 40 | 0.0012 | 0.01 | 0.024 | 0.081 | 0.521 | 39.8 |
| t | 0.02 | 0.01 | 10 | 0.0033 | 0.0061 | 0.008 | 0.025 | 0.168 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.0017 | 0.0051 | 0.009 | 0.027 | 0.210 | 19.9 |
| t | 0.02 | 0.01 | 30 | 0.00145 | 0.0046 | 0.010 | 0.029 | 0.244 | 29.9 |
| t | 0.02 | 0.01 | 40 | 0.0015 | 0.004 | 0.010 | 0.032 | 0.290 | 39.9 |
| wilcoxon | 0 | 0.01 | 10 | 0.00335 | 0.0072 | 0.026 | 0.137 | 0.826 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00255 | 0.0082 | 0.031 | 0.187 | 0.992 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.00175 | 0.0097 | 0.033 | 0.219 | 1.000 | 29.8 |
| wilcoxon | 0 | 0.01 | 40 | 0.00165 | 0.0088 | 0.034 | 0.246 | 1.000 | 39.8 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.0046 | 0.0052 | 0.009 | 0.060 | 0.700 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00265 | 0.005 | 0.010 | 0.066 | 0.927 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.002 | 0.006 | 0.010 | 0.067 | 0.985 | 29.9 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.00165 | 0.0079 | 0.011 | 0.073 | 0.998 | 39.8 |

## Rules under the dev2-after null (74 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 3.2e-09 | 3.2e-09 | 0.000 | 0.424 | 0.980 | 3.2 | 5.1 |
| 20 | 3.2e-09 | 3.2e-09 | 0.000 | 0.540 | 0.999 | 5.1 | 5.2 |
| 30 | 3.2e-09 | 3.2e-09 | 0.000 | 0.569 | 1.000 | 5.1 | 5.2 |
| 40 | 3.2e-09 | 3.2e-09 | 0.000 | 0.595 | 1.000 | 5.1 | 5.2 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.089 | 0.089 | 0.438 | 0.574 | 1.000 | 3.0 | 5.6 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.22 | 0.22 | 0.869 | 0.959 | 1.000 | 11.7 | 10.7 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.38 | 0.38 | 0.985 | 0.999 | 1.000 | 21.2 | 12.0 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.49 | 0.49 | 0.997 | 1.000 | 1.000 | 27.2 | 12.4 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.031 | 0.031 | 0.297 | 0.446 | 1.000 | 3.2 | 7.2 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.06 | 0.06 | 0.627 | 0.824 | 1.000 | 9.9 | 14.6 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.13 | 0.13 | 0.894 | 0.979 | 1.000 | 18.9 | 16.6 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.21 | 0.21 | 0.973 | 0.998 | 1.000 | 27.4 | 17.1 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.015 | 0.015 | 0.347 | 0.567 | 1.000 | 6.8 | 14.2 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.044 | 0.044 | 0.738 | 0.921 | 1.000 | 16.6 | 21.0 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.082 | 0.082 | 0.914 | 0.989 | 1.000 | 26.1 | 22.6 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.089 | 0.465 | 0.823 | 1.2 | 5.2 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 5.9e-06 | 5.9e-06 | 0.223 | 0.900 | 0.999 | 5.7 | 11.5 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 4.7e-06 | 4.7e-06 | 0.383 | 0.992 | 1.000 | 11.4 | 13.4 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 2.2e-06 | 2.2e-06 | 0.490 | 0.999 | 1.000 | 15.7 | 14.0 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.031 | 0.330 | 0.758 | 1.2 | 6.5 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 4.5e-08 | 4.5e-08 | 0.060 | 0.687 | 0.987 | 4.3 | 14.7 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 5.2e-08 | 5.2e-08 | 0.134 | 0.929 | 1.000 | 8.6 | 18.3 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 3.6e-08 | 3.6e-08 | 0.207 | 0.986 | 1.000 | 12.8 | 19.5 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 6.2e-10 | 6.2e-10 | 0.015 | 0.404 | 0.912 | 2.5 | 13.1 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 4.7e-10 | 4.7e-10 | 0.044 | 0.804 | 0.999 | 7.2 | 22.3 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 3.4e-10 | 3.4e-10 | 0.082 | 0.949 | 1.000 | 11.4 | 25.3 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.089 | 0.609 | 1.0 | 3.0 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | <1e-12 | <1e-12 | 0.000 | 0.223 | 0.975 | 4.3 | 11.7 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.000 | 0.383 | 1.000 | 8.6 | 21.2 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.000 | 0.490 | 1.000 | 11.8 | 27.2 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.031 | 0.493 | 1.0 | 3.2 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.060 | 0.873 | 3.2 | 9.9 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.134 | 0.990 | 6.4 | 18.9 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.207 | 0.999 | 9.7 | 27.4 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.015 | 0.642 | 2.0 | 6.8 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.044 | 0.955 | 5.4 | 16.6 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.082 | 0.996 | 8.6 | 26.1 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 20000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.0029 | 0.011 | 0.329 | 0.660 | 0.911 | 10.0 |
| t | 0 | 0.01 | 20 | 0.0016 | 0.012 | 0.382 | 0.823 | 0.919 | 19.9 |
| t | 0 | 0.01 | 30 | 0.00125 | 0.01 | 0.419 | 0.863 | 0.921 | 29.8 |
| t | 0 | 0.01 | 40 | 0.001 | 0.0098 | 0.476 | 0.871 | 0.915 | 39.8 |
| t | 0.02 | 0.01 | 10 | 0.00295 | <1e-12 | 0.011 | 0.472 | 0.869 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.0016 | <1e-12 | 0.009 | 0.556 | 0.910 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.00125 | <1e-12 | 0.009 | 0.667 | 0.909 | 30.0 |
| t | 0.02 | 0.01 | 40 | 0.00105 | <1e-12 | 0.010 | 0.727 | 0.904 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00425 | 0.01 | 0.206 | 0.697 | 0.986 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 0.00265 | 0.01 | 0.247 | 0.974 | 1.000 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 0.00195 | 0.0093 | 0.290 | 0.998 | 1.000 | 39.8 |
| wilcoxon | 0.02 | 0.01 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00395 | <1e-12 | 0.010 | 0.330 | 0.953 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00255 | <1e-12 | 0.011 | 0.459 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.00225 | <1e-12 | 0.009 | 0.566 | 1.000 | 40.0 |

## Rules under the dev3-before null (83 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.15 | 0.15 | 0.175 | 0.286 | 0.407 | 5.9 | 5.9 |
| 20 | 0.18 | 0.18 | 0.215 | 0.368 | 0.529 | 9.8 | 8.7 |
| 30 | 0.19 | 0.19 | 0.221 | 0.384 | 0.559 | 12.2 | 10.3 |
| 40 | 0.19 | 0.19 | 0.224 | 0.396 | 0.585 | 15.9 | 12.5 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.010 | 0.011 | 2.0 | 2.1 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.077 | 0.077 | 0.092 | 0.157 | 0.180 | 11.2 | 12.1 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.17 | 0.17 | 0.201 | 0.330 | 0.377 | 21.2 | 22.0 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.23 | 0.23 | 0.275 | 0.442 | 0.501 | 28.2 | 28.4 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.003 | 0.004 | 2.0 | 2.2 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.011 | 0.011 | 0.014 | 0.031 | 0.039 | 8.7 | 9.6 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.034 | 0.034 | 0.044 | 0.096 | 0.118 | 17.0 | 18.9 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.059 | 0.059 | 0.077 | 0.165 | 0.204 | 25.3 | 27.6 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.001 | 0.001 | 0.001 | 0.005 | 0.006 | 5.9 | 6.4 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.0068 | 0.0068 | 0.009 | 0.026 | 0.034 | 14.4 | 16.2 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.015 | 0.015 | 0.021 | 0.058 | 0.078 | 22.9 | 25.8 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.011 | 2.0 | 2.0 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.038 | 0.038 | 0.077 | 0.092 | 0.180 | 10.4 | 11.4 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.077 | 0.077 | 0.169 | 0.201 | 0.377 | 19.8 | 21.5 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.1 | 0.1 | 0.231 | 0.275 | 0.501 | 26.8 | 28.4 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.004 | 2.0 | 2.0 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.004 | 0.004 | 0.011 | 0.014 | 0.039 | 8.0 | 8.9 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.011 | 0.011 | 0.034 | 0.044 | 0.118 | 15.5 | 17.5 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.018 | 0.018 | 0.059 | 0.077 | 0.204 | 23.0 | 25.9 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.0003 | 0.0003 | 0.001 | 0.001 | 0.006 | 5.5 | 6.0 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.0017 | 0.0017 | 0.007 | 0.009 | 0.034 | 13.1 | 14.8 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.0033 | 0.0033 | 0.015 | 0.021 | 0.078 | 20.6 | 23.6 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.010 | 2.0 | 2.0 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 0.025 | 0.025 | 0.031 | 0.077 | 0.157 | 9.9 | 11.2 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 0.048 | 0.048 | 0.062 | 0.169 | 0.330 | 19.1 | 21.2 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 0.06 | 0.06 | 0.079 | 0.231 | 0.442 | 25.9 | 28.2 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.003 | 2.0 | 2.0 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.0022 | 0.0022 | 0.003 | 0.011 | 0.031 | 7.6 | 8.7 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.006 | 0.006 | 0.008 | 0.034 | 0.096 | 14.7 | 17.0 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0087 | 0.0087 | 0.013 | 0.059 | 0.165 | 21.8 | 25.3 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.00015 | 0.00015 | 0.000 | 0.001 | 0.005 | 5.2 | 5.9 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.00075 | 0.00075 | 0.001 | 0.007 | 0.026 | 12.4 | 14.4 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.0014 | 0.0014 | 0.002 | 0.015 | 0.058 | 19.5 | 22.9 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 20000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.0034 | 0.01 | 0.016 | 0.035 | 0.113 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00175 | 0.009 | 0.020 | 0.051 | 0.149 | 19.9 |
| t | 0 | 0.01 | 30 | 0.00125 | 0.011 | 0.024 | 0.065 | 0.233 | 29.8 |
| t | 0 | 0.01 | 40 | 0.0012 | 0.01 | 0.023 | 0.071 | 0.301 | 39.8 |
| t | 0.02 | 0.01 | 10 | 0.00335 | 0.0042 | 0.011 | 0.026 | 0.087 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.0018 | 0.004 | 0.010 | 0.032 | 0.102 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.00125 | 0.0046 | 0.011 | 0.038 | 0.169 | 29.9 |
| t | 0.02 | 0.01 | 40 | 0.0011 | 0.0036 | 0.011 | 0.036 | 0.203 | 39.9 |
| wilcoxon | 0 | 0.01 | 10 | 0.0057 | 0.0093 | 0.016 | 0.052 | 0.157 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00295 | 0.01 | 0.020 | 0.070 | 0.246 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.0018 | 0.012 | 0.023 | 0.091 | 0.375 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 0.00165 | 0.012 | 0.023 | 0.105 | 0.506 | 39.8 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00575 | 0.0041 | 0.008 | 0.021 | 0.099 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.0024 | 0.0046 | 0.010 | 0.029 | 0.166 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00195 | 0.0056 | 0.010 | 0.028 | 0.224 | 29.9 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.0016 | 0.0044 | 0.011 | 0.038 | 0.326 | 39.9 |

## Rules under the dev3-after null (75 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.0045 | 0.0045 | 0.035 | 0.193 | 0.728 | 4.7 | 5.5 |
| 20 | 0.0047 | 0.0047 | 0.040 | 0.243 | 0.869 | 8.2 | 6.6 |
| 30 | 0.0047 | 0.0047 | 0.040 | 0.251 | 0.903 | 9.8 | 7.1 |
| 40 | 0.0047 | 0.0047 | 0.040 | 0.256 | 0.932 | 12.1 | 7.6 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.017 | 0.017 | 0.061 | 0.188 | 0.458 | 2.9 | 4.3 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.053 | 0.053 | 0.209 | 0.550 | 0.906 | 10.1 | 12.9 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.095 | 0.095 | 0.384 | 0.815 | 0.993 | 19.7 | 19.0 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.12 | 0.12 | 0.498 | 0.911 | 0.999 | 26.8 | 21.5 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0039 | 0.0039 | 0.021 | 0.096 | 0.326 | 3.0 | 4.7 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.0074 | 0.0074 | 0.053 | 0.251 | 0.693 | 7.8 | 12.8 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.017 | 0.017 | 0.130 | 0.510 | 0.934 | 15.5 | 21.4 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.025 | 0.025 | 0.209 | 0.699 | 0.988 | 23.1 | 27.4 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.0011 | 0.0011 | 0.012 | 0.089 | 0.408 | 5.3 | 9.4 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.003 | 0.003 | 0.041 | 0.280 | 0.812 | 13.0 | 21.4 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.0053 | 0.0053 | 0.082 | 0.479 | 0.953 | 20.7 | 30.5 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.008 | 0.008 | 0.017 | 0.115 | 0.318 | 2.6 | 3.9 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.017 | 0.017 | 0.053 | 0.383 | 0.775 | 8.8 | 12.8 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.024 | 0.024 | 0.095 | 0.641 | 0.956 | 17.5 | 20.8 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.028 | 0.028 | 0.123 | 0.770 | 0.988 | 24.0 | 24.8 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0013 | 0.0013 | 0.004 | 0.050 | 0.197 | 2.6 | 4.1 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.0015 | 0.0015 | 0.007 | 0.136 | 0.481 | 6.7 | 11.6 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.0029 | 0.0029 | 0.017 | 0.311 | 0.790 | 13.3 | 20.9 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0035 | 0.0035 | 0.025 | 0.469 | 0.923 | 19.9 | 28.7 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.0002 | 0.0002 | 0.001 | 0.039 | 0.225 | 4.5 | 8.1 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.00035 | 0.00035 | 0.003 | 0.135 | 0.577 | 11.1 | 19.5 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.00047 | 0.00047 | 0.005 | 0.256 | 0.805 | 17.7 | 29.5 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.002 | 0.017 | 0.188 | 2.0 | 2.9 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00011 | 0.00011 | 0.004 | 0.053 | 0.550 | 6.5 | 10.1 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 0.00011 | 0.00011 | 0.004 | 0.095 | 0.815 | 12.8 | 19.7 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 7.1e-05 | 7.1e-05 | 0.004 | 0.123 | 0.911 | 17.6 | 26.8 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.004 | 0.096 | 2.0 | 3.0 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 2e-06 | 2e-06 | 0.000 | 0.007 | 0.251 | 4.9 | 7.8 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 2.8e-06 | 2.8e-06 | 0.000 | 0.017 | 0.510 | 9.6 | 15.5 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 2e-06 | 2e-06 | 0.000 | 0.025 | 0.699 | 14.4 | 23.1 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 4.6e-08 | 4.6e-08 | 0.000 | 0.001 | 0.089 | 3.4 | 5.3 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 6.4e-08 | 6.4e-08 | 0.000 | 0.003 | 0.280 | 8.1 | 13.0 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 5.4e-08 | 5.4e-08 | 0.000 | 0.005 | 0.479 | 12.8 | 20.7 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 20000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.0029 | 0.0099 | 0.038 | 0.155 | 0.593 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00165 | 0.0097 | 0.050 | 0.271 | 0.924 | 19.9 |
| t | 0 | 0.01 | 30 | 0.0012 | 0.011 | 0.070 | 0.446 | 0.996 | 29.8 |
| t | 0 | 0.01 | 40 | 0.00105 | 0.0099 | 0.085 | 0.607 | 1.000 | 39.8 |
| t | 0.02 | 0.01 | 10 | 0.00315 | 0.0018 | 0.010 | 0.065 | 0.406 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.00165 | 0.0011 | 0.010 | 0.101 | 0.749 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.00125 | 0.0013 | 0.010 | 0.142 | 0.926 | 30.0 |
| t | 0.02 | 0.01 | 40 | 0.00105 | 0.0006 | 0.010 | 0.182 | 0.986 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00545 | 0.0087 | 0.035 | 0.135 | 0.443 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00315 | 0.011 | 0.051 | 0.280 | 0.930 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.00205 | 0.0089 | 0.063 | 0.420 | 0.993 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 0.00175 | 0.011 | 0.085 | 0.575 | 1.000 | 39.8 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.0063 | 0.003 | 0.009 | 0.078 | 0.297 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.0029 | 0.0016 | 0.011 | 0.122 | 0.792 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.0024 | 0.001 | 0.011 | 0.166 | 0.951 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.00175 | 0.0006 | 0.011 | 0.226 | 0.992 | 40.0 |

## Rules under the dev4-before null (72 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 7.4e-10 | 7.4e-10 | 0.001 | 0.244 | 1.000 | 3.2 | 5.0 |
| 20 | 7.4e-10 | 7.4e-10 | 0.001 | 0.310 | 1.000 | 5.1 | 5.0 |
| 30 | 7.4e-10 | 7.4e-10 | 0.001 | 0.323 | 1.000 | 5.1 | 5.0 |
| 40 | 7.4e-10 | 7.4e-10 | 0.001 | 0.332 | 1.000 | 5.1 | 5.0 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.034 | 0.034 | 0.603 | 1.000 | 1.000 | 2.0 | 7.0 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.087 | 0.087 | 0.973 | 1.000 | 1.000 | 10.5 | 8.0 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.15 | 0.15 | 0.999 | 1.000 | 1.000 | 20.3 | 9.0 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.2 | 0.2 | 1.000 | 1.000 | 1.000 | 27.3 | 9.0 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.009 | 0.009 | 0.486 | 1.000 | 1.000 | 2.1 | 10.0 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.015 | 0.015 | 0.867 | 1.000 | 1.000 | 8.2 | 12.0 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.034 | 0.034 | 0.989 | 1.000 | 1.000 | 16.3 | 12.0 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.051 | 0.051 | 0.999 | 1.000 | 1.000 | 24.3 | 12.0 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.0029 | 0.0029 | 0.631 | 1.000 | 1.000 | 5.4 | 14.0 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.0074 | 0.0074 | 0.952 | 1.000 | 1.000 | 13.8 | 15.0 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.013 | 0.013 | 0.995 | 1.000 | 1.000 | 22.0 | 16.0 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00037 | 0.00037 | 0.034 | 0.667 | 1.000 | 1.1 | 5.9 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00046 | 0.00046 | 0.087 | 0.987 | 1.000 | 6.7 | 9.9 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.00039 | 0.00039 | 0.152 | 1.000 | 1.000 | 13.4 | 10.9 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0003 | 0.0003 | 0.199 | 1.000 | 1.000 | 18.4 | 11.3 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 2.4e-05 | 2.4e-05 | 0.009 | 0.562 | 1.000 | 1.1 | 7.8 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 1.2e-05 | 1.2e-05 | 0.015 | 0.920 | 1.000 | 5.0 | 14.2 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 1.6e-05 | 1.6e-05 | 0.034 | 0.996 | 1.000 | 10.0 | 15.1 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 1.4e-05 | 1.4e-05 | 0.051 | 1.000 | 1.000 | 15.1 | 15.3 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 9e-07 | 9e-07 | 0.003 | 0.727 | 1.000 | 3.1 | 14.9 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 6.6e-07 | 6.6e-07 | 0.007 | 0.979 | 1.000 | 8.4 | 19.3 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 4.8e-07 | 4.8e-07 | 0.013 | 0.999 | 1.000 | 13.4 | 20.3 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.034 | 1.000 | 1.0 | 2.0 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | <1e-12 | <1e-12 | 0.000 | 0.087 | 1.000 | 4.2 | 10.5 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.000 | 0.152 | 1.000 | 8.5 | 20.3 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.000 | 0.199 | 1.000 | 11.6 | 27.3 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.009 | 1.000 | 1.0 | 2.1 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.015 | 1.000 | 3.2 | 8.2 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.034 | 1.000 | 6.4 | 16.3 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.051 | 1.000 | 9.5 | 24.3 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.003 | 1.000 | 2.1 | 5.4 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.007 | 1.000 | 5.3 | 13.8 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.013 | 1.000 | 8.5 | 22.0 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 20000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.0031 | 0.011 | 0.311 | 0.964 | 1.000 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00165 | 0.012 | 0.562 | 1.000 | 1.000 | 19.9 |
| t | 0 | 0.01 | 30 | 0.0012 | 0.01 | 0.777 | 1.000 | 1.000 | 29.8 |
| t | 0 | 0.01 | 40 | 0.0011 | 0.0089 | 0.900 | 1.000 | 1.000 | 39.8 |
| t | 0.02 | 0.01 | 10 | 0.00285 | 0.00015 | 0.011 | 0.641 | 1.000 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.00165 | 0.0001 | 0.010 | 0.923 | 1.000 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.0012 | 5e-05 | 0.010 | 0.995 | 1.000 | 30.0 |
| t | 0.02 | 0.01 | 40 | 0.00105 | 5e-05 | 0.010 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.0061 | 0.0077 | 0.313 | 0.628 | 0.620 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00355 | 0.0085 | 0.637 | 0.995 | 0.994 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.0023 | 0.0093 | 0.833 | 1.000 | 1.000 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 0.002 | 0.01 | 0.931 | 1.000 | 1.000 | 39.8 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.0055 | <1e-12 | 0.006 | 0.357 | 0.621 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.0035 | <1e-12 | 0.009 | 0.924 | 0.995 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00255 | <1e-12 | 0.010 | 0.998 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.0021 | <1e-12 | 0.010 | 1.000 | 1.000 | 40.0 |

## Rules under the dev4-after null (72 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | <1e-12 | <1e-12 | 0.000 | 0.011 | 0.991 | 3.0 | 5.1 |
| 20 | <1e-12 | <1e-12 | 0.000 | 0.011 | 1.000 | 5.0 | 5.1 |
| 30 | <1e-12 | <1e-12 | 0.000 | 0.011 | 1.000 | 5.0 | 5.1 |
| 40 | <1e-12 | <1e-12 | 0.000 | 0.011 | 1.000 | 5.0 | 5.1 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0016 | 0.0016 | 0.231 | 0.663 | 1.000 | 1.7 | 5.9 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0011 | 0.0011 | 0.629 | 0.988 | 1.000 | 6.7 | 10.0 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.00076 | 0.00076 | 0.877 | 1.000 | 1.000 | 13.4 | 10.9 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0006 | 0.0006 | 0.950 | 1.000 | 1.000 | 18.4 | 11.3 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0001 | 0.0001 | 0.127 | 0.559 | 1.000 | 1.7 | 7.8 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 3.3e-05 | 3.3e-05 | 0.322 | 0.922 | 1.000 | 5.0 | 14.3 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 3.8e-05 | 3.8e-05 | 0.612 | 0.996 | 1.000 | 10.0 | 15.1 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 3.4e-05 | 3.4e-05 | 0.795 | 1.000 | 1.000 | 15.1 | 15.3 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 3.4e-06 | 3.4e-06 | 0.127 | 0.727 | 1.000 | 3.3 | 14.9 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.9e-06 | 1.9e-06 | 0.374 | 0.980 | 1.000 | 8.4 | 19.3 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 1.2e-06 | 1.2e-06 | 0.600 | 0.999 | 1.000 | 13.4 | 20.3 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 1.4e-09 | 1.4e-09 | 0.002 | 0.477 | 1.000 | 1.0 | 5.2 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 7.7e-11 | 7.7e-11 | 0.001 | 0.925 | 1.000 | 4.2 | 11.4 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 4.4e-12 | 4.4e-12 | 0.001 | 0.996 | 1.000 | 8.5 | 13.0 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 4.3e-12 | 4.3e-12 | 0.001 | 1.000 | 1.000 | 11.6 | 13.5 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.351 | 1.000 | 1.0 | 6.5 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.735 | 1.000 | 3.2 | 14.8 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.953 | 1.000 | 6.4 | 17.8 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.993 | 1.000 | 9.5 | 18.7 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.452 | 1.000 | 2.1 | 13.5 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.853 | 1.000 | 5.3 | 22.0 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.970 | 1.000 | 8.5 | 24.4 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.002 | 0.663 | 1.0 | 1.7 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | <1e-12 | <1e-12 | 0.000 | 0.001 | 0.988 | 4.1 | 6.7 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.000 | 0.001 | 1.000 | 8.1 | 13.4 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.000 | 0.001 | 1.000 | 11.2 | 18.4 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.559 | 1.0 | 1.7 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.922 | 3.0 | 5.0 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.996 | 6.1 | 10.0 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 9.1 | 15.1 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.727 | 2.0 | 3.3 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.980 | 5.1 | 8.4 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.999 | 8.1 | 13.4 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 20000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00335 | 0.0089 | 0.604 | 0.999 | 1.000 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00165 | 0.01 | 0.869 | 1.000 | 1.000 | 19.9 |
| t | 0 | 0.01 | 30 | 0.0012 | 0.0093 | 0.974 | 1.000 | 1.000 | 29.9 |
| t | 0 | 0.01 | 40 | 0.00105 | 0.0098 | 0.996 | 1.000 | 1.000 | 39.8 |
| t | 0.02 | 0.01 | 10 | 0.00325 | <1e-12 | 0.011 | 0.892 | 1.000 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.00175 | <1e-12 | 0.011 | 0.997 | 1.000 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.00125 | <1e-12 | 0.010 | 1.000 | 1.000 | 30.0 |
| t | 0.02 | 0.01 | 40 | 0.0012 | <1e-12 | 0.012 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.0045 | 0.01 | 0.583 | 0.999 | 1.000 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00235 | 0.012 | 0.905 | 1.000 | 1.000 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.0019 | 0.0097 | 0.982 | 1.000 | 1.000 | 29.8 |
| wilcoxon | 0 | 0.01 | 40 | 0.0015 | 0.0097 | 0.998 | 1.000 | 1.000 | 39.8 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00425 | <1e-12 | 0.010 | 0.863 | 1.000 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00235 | <1e-12 | 0.011 | 0.996 | 1.000 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00155 | <1e-12 | 0.012 | 1.000 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.00155 | <1e-12 | 0.010 | 1.000 | 1.000 | 40.0 |

