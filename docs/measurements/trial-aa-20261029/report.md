# A/A rounds of paired trials: the null, the current rule, candidate rules

x = log(t_AA / t_preference) per round: an equal challenger's log ratio. Rates are per contest, for independent rounds drawn from the measured null round by round (a process's first three contest rounds each from its own sample, later rounds and confirmations by the order's parity: Null), unless a line says otherwise; m equal challengers are taken as independent (an upper bound). Powers are for one challenger of the stated gain, its noise the A/A arm's.

## Candidate rules against D8 (no looser than the current measured false-switch rate)

False-switch rates are per contest at gain 0 for each group's m equal challengers (Holm: alpha / m per arm; the current rule with its confirmation). "Every group": the test's rate is no larger than the current rule's under each group's null; "worst": its largest rate is no larger than the current rule's largest (0.00091, dev2-replay). "With the contest effect": the same two with each group's contest effect added to both rules (an upper bound for each; the current rule's largest is then 0.057). "Keeps power": its power at 5% and 10% is at least the current rule's under every group's null, exactly; where it is not, the largest shortfall and where. Listed: every rule that meets "every group", those that meet "worst" and keep the power, and the rules compared below (the per-group rates of all are below). Power for one challenger of the gain, worst group / best group; rounds: the largest expected count at gain 0 and at 5%, and the rounds a challenger that loses every round runs (the usual case: on most banks the CPU's challengers are 1.1-2.2x slower), which with each group's cost of a round (below) is the trial's overhead.

| rule | every group | worst | with the contest effect: every / worst | keeps power | power (worst / best) 2% | power (worst / best) 5% | power (worst / best) 10% | rounds at 0 / 5% | rounds, all lost |
|---|---|---|---|---|---|---|---|---|---|
| current (TIE 5%, 75%, 5/10, confirm) | (reference) | (reference) | (reference) | (reference) | 0.000 / 0.003 | 0.023 / 0.074 | 0.570 / 0.998 | 4.4 / 5.4 | 3 |
| sign, delta 0, alpha 0.0001, cap 40 | no | yes | no / no | yes | 0.001 / 1.000 | 0.090 / 1.000 | 0.829 / 1.000 | 14.8 / 29.1 | 7 |
| sign, delta 0.01, alpha 0.003, cap 30 | no | yes | no / no | yes | 0.002 / 0.945 | 0.148 / 1.000 | 0.837 / 1.000 | 11.1 / 20.6 | 6 |
| sign, delta 0.01, alpha 0.003, cap 40 | no | yes | no / no | yes | 0.002 / 0.995 | 0.256 / 1.000 | 0.966 / 1.000 | 18.4 / 29.8 | 10 |
| sign, delta 0.01, alpha 0.002, cap 30 | no | yes | no / no | yes | 0.002 / 0.937 | 0.131 / 1.000 | 0.818 / 1.000 | 11.1 / 20.9 | 6 |
| sign, delta 0.01, alpha 0.002, cap 40 | no | yes | no / no | yes | 0.001 / 0.988 | 0.198 / 1.000 | 0.940 / 1.000 | 16.5 / 28.5 | 9 |
| sign, delta 0.01, alpha 0.001, cap 30 | no | yes | no / no | yes | 0.001 / 0.925 | 0.102 / 1.000 | 0.793 / 1.000 | 11.1 / 22.1 | 6 |
| sign, delta 0.01, alpha 0.001, cap 40 | no | yes | no / no | yes | 0.001 / 0.983 | 0.152 / 1.000 | 0.922 / 1.000 | 16.5 / 30.0 | 9 |
| sign, delta 0.01, alpha 0.0001, cap 40 | no | yes | no / no | yes | 0.000 / 0.913 | 0.048 / 1.000 | 0.754 / 1.000 | 12.9 / 29.0 | 7 |
| sign, delta 0.015, alpha 0.005, cap 30 | no | yes | no / no | yes | 0.000 / 0.580 | 0.210 / 1.000 | 0.886 / 1.000 | 12.3 / 21.9 | 7 |
| sign, delta 0.015, alpha 0.005, cap 40 | no | yes | no / no | yes | 0.000 / 0.751 | 0.294 / 1.000 | 0.963 / 1.000 | 17.6 / 28.7 | 10 |
| sign, delta 0.015, alpha 0.003, cap 30 | no | yes | no / no | yes | 0.000 / 0.461 | 0.145 / 1.000 | 0.810 / 1.000 | 10.6 / 20.7 | 6 |
| sign, delta 0.015, alpha 0.003, cap 40 | no | yes | no / no | yes | 0.000 / 0.713 | 0.252 / 1.000 | 0.955 / 1.000 | 17.6 / 29.7 | 10 |
| sign, delta 0.015, alpha 0.002, cap 30 | no | yes | no / no | yes | 0.000 / 0.436 | 0.127 / 1.000 | 0.789 / 1.000 | 10.6 / 21.0 | 6 |
| sign, delta 0.015, alpha 0.002, cap 40 | no | yes | no / no | yes | 0.000 / 0.627 | 0.194 / 1.000 | 0.924 / 1.000 | 15.8 / 28.5 | 9 |
| sign, delta 0.015, alpha 0.001, cap 30 | no | yes | no / no | yes | 0.000 / 0.386 | 0.100 / 1.000 | 0.761 / 1.000 | 10.6 / 22.0 | 6 |
| sign, delta 0.015, alpha 0.001, cap 40 | no | yes | no / no | yes | 0.000 / 0.566 | 0.149 / 1.000 | 0.902 / 1.000 | 15.8 / 29.8 | 9 |
| sign, delta 0.02, alpha 0.01, cap 20 | no | no | no / no | no: 0.00029 short at 10% (dev1-replay-solo) | 0.001 / 0.008 | 0.087 / 0.998 | 0.681 / 1.000 | 6.8 / 13.2 | 4 |
| sign, delta 0.02, alpha 0.01, cap 30 | no | yes | no / no | yes | 0.000 / 0.009 | 0.139 / 1.000 | 0.893 / 1.000 | 11.8 / 20.4 | 7 |
| sign, delta 0.02, alpha 0.01, cap 40 | no | yes | no / no | yes | 0.000 / 0.009 | 0.199 / 1.000 | 0.975 / 1.000 | 18.3 / 29.3 | 11 |
| sign, delta 0.02, alpha 0.005, cap 30 | no | yes | no / no | yes | 0.000 / 0.004 | 0.099 / 1.000 | 0.863 / 1.000 | 11.8 / 21.7 | 7 |
| sign, delta 0.02, alpha 0.005, cap 40 | no | yes | no / no | yes | 0.000 / 0.005 | 0.137 / 1.000 | 0.951 / 1.000 | 16.7 / 28.7 | 10 |
| sign, delta 0.02, alpha 0.003, cap 30 | no | yes | no / no | yes | 0.000 / 0.002 | 0.063 / 1.000 | 0.779 / 1.000 | 10.1 / 20.1 | 6 |
| sign, delta 0.02, alpha 0.003, cap 40 | no | yes | no / no | yes | 0.000 / 0.003 | 0.108 / 1.000 | 0.942 / 1.000 | 16.7 / 29.7 | 10 |
| sign, delta 0.02, alpha 0.002, cap 30 | no | yes | no / no | yes | 0.000 / 0.002 | 0.054 / 1.000 | 0.757 / 1.000 | 10.1 / 20.3 | 6 |
| sign, delta 0.02, alpha 0.002, cap 40 | no | yes | no / no | yes | 0.000 / 0.002 | 0.079 / 1.000 | 0.904 / 1.000 | 15.0 / 28.2 | 9 |
| sign, delta 0.02, alpha 0.001, cap 30 | no | yes | no / no | yes | 0.000 / 0.001 | 0.039 / 1.000 | 0.725 / 1.000 | 10.1 / 21.0 | 6 |
| sign, delta 0.02, alpha 0.001, cap 40 | no | yes | no / no | yes | 0.000 / 0.001 | 0.055 / 1.000 | 0.878 / 1.000 | 15.0 / 29.4 | 9 |
| sign, delta 0.02, alpha 0.0001, cap 30 | yes | yes | no / yes | no: 0.25 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.007 / 0.989 | 0.394 / 1.000 | 6.8 / 21.2 | 4 |
| sign, delta 0.02, alpha 0.0001, cap 40 | yes | yes | no / no | no: 0.044 short at 5% (dev1-ladder) | 0.000 / 0.000 | 0.013 / 1.000 | 0.672 / 1.000 | 11.8 / 26.4 | 7 |
| sign, delta 0.025, alpha 0.02, cap 30 | no | yes | no / no | yes | 0.000 / 0.007 | 0.135 / 1.000 | 0.930 / 1.000 | 12.8 / 21.0 | 8 |
| sign, delta 0.025, alpha 0.02, cap 40 | no | yes | no / no | yes | 0.000 / 0.007 | 0.169 / 1.000 | 0.978 / 1.000 | 17.5 / 27.7 | 11 |
| sign, delta 0.025, alpha 0.01, cap 30 | no | yes | no / no | yes | 0.000 / 0.004 | 0.083 / 1.000 | 0.873 / 1.000 | 11.2 / 20.3 | 7 |
| sign, delta 0.025, alpha 0.01, cap 40 | no | yes | no / no | yes | 0.000 / 0.003 | 0.115 / 1.000 | 0.967 / 1.000 | 17.5 / 29.3 | 11 |
| sign, delta 0.025, alpha 0.005, cap 30 | no | yes | no / no | yes | 0.000 / 0.002 | 0.056 / 1.000 | 0.839 / 1.000 | 11.2 / 21.3 | 7 |
| sign, delta 0.025, alpha 0.005, cap 40 | no | yes | no / no | yes | 0.000 / 0.002 | 0.074 / 1.000 | 0.938 / 1.000 | 15.9 / 28.4 | 10 |
| sign, delta 0.025, alpha 0.003, cap 30 | no | yes | no / no | yes | 0.000 / 0.001 | 0.034 / 1.000 | 0.749 / 1.000 | 9.6 / 19.8 | 6 |
| sign, delta 0.025, alpha 0.003, cap 40 | no | yes | no / no | yes | 0.000 / 0.001 | 0.056 / 1.000 | 0.926 / 1.000 | 15.9 / 29.4 | 10 |
| sign, delta 0.025, alpha 0.002, cap 40 | no | yes | no / no | yes | 0.000 / 0.001 | 0.039 / 1.000 | 0.883 / 1.000 | 14.3 / 27.6 | 9 |
| sign, delta 0.025, alpha 0.0001, cap 20 | yes | yes | no / yes | no: 0.48 short at 10% (dev1-ladder) | 0.000 / 0.000 | 0.002 / 0.878 | 0.162 / 0.984 | 3.6 / 16.1 | 2 |
| sign, delta 0.025, alpha 0.0001, cap 30 | yes | yes | no / yes | no: 0.28 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.003 / 0.989 | 0.360 / 1.000 | 6.5 / 21.2 | 4 |
| sign, delta 0.025, alpha 0.0001, cap 40 | yes | yes | no / yes | no: 0.056 short at 5% (dev1-ladder) | 0.000 / 0.000 | 0.005 / 1.000 | 0.631 / 1.000 | 11.2 / 28.8 | 7 |
| sign, delta 0.03, alpha 0.05, cap 40 | no | yes | no / no | yes | 0.000 / 0.008 | 0.178 / 1.000 | 0.987 / 1.000 | 18.2 / 27.3 | 12 |
| sign, delta 0.03, alpha 0.02, cap 20 | no | yes | no / no | yes | 0.000 / 0.004 | 0.056 / 0.998 | 0.676 / 1.000 | 6.2 / 12.7 | 4 |
| sign, delta 0.03, alpha 0.02, cap 30 | no | yes | no / no | yes | 0.000 / 0.003 | 0.083 / 1.000 | 0.908 / 1.000 | 12.2 / 20.8 | 8 |
| sign, delta 0.03, alpha 0.02, cap 40 | no | yes | no / no | yes | 0.000 / 0.003 | 0.100 / 1.000 | 0.967 / 1.000 | 16.7 / 27.4 | 11 |
| sign, delta 0.03, alpha 0.01, cap 30 | no | yes | no / no | yes | 0.000 / 0.001 | 0.049 / 1.000 | 0.841 / 1.000 | 10.7 / 19.5 | 7 |
| sign, delta 0.03, alpha 0.01, cap 40 | no | yes | no / no | yes | 0.000 / 0.001 | 0.062 / 1.000 | 0.953 / 1.000 | 16.7 / 28.8 | 11 |
| sign, delta 0.03, alpha 0.003, cap 20 | no | yes | no / yes | no: 0.21 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.014 / 0.985 | 0.427 / 0.999 | 4.8 / 13.4 | 3 |
| sign, delta 0.03, alpha 0.003, cap 30 | yes | yes | no / no | no: 0.034 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.018 / 1.000 | 0.703 / 1.000 | 9.2 / 20.8 | 6 |
| sign, delta 0.03, alpha 0.003, cap 40 | yes | yes | no / no | no: 0.015 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.027 / 1.000 | 0.899 / 1.000 | 15.2 / 28.2 | 10 |
| sign, delta 0.03, alpha 0.002, cap 20 | yes | yes | no / yes | no: 0.27 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.008 / 0.981 | 0.375 / 0.998 | 4.8 / 14.8 | 3 |
| sign, delta 0.03, alpha 0.002, cap 30 | yes | yes | no / no | no: 0.039 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.015 / 1.000 | 0.676 / 1.000 | 9.2 / 21.2 | 6 |
| sign, delta 0.03, alpha 0.002, cap 40 | yes | yes | no / no | no: 0.029 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.019 / 1.000 | 0.847 / 1.000 | 13.7 / 26.6 | 9 |
| sign, delta 0.03, alpha 0.001, cap 20 | yes | yes | no / yes | no: 0.3 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.006 / 0.977 | 0.342 / 0.998 | 4.8 / 15.3 | 3 |
| sign, delta 0.03, alpha 0.001, cap 30 | yes | yes | no / yes | no: 0.046 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.009 / 1.000 | 0.639 / 1.000 | 9.2 / 22.5 | 6 |
| sign, delta 0.03, alpha 0.001, cap 40 | yes | yes | no / no | no: 0.04 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.012 / 1.000 | 0.810 / 1.000 | 13.7 / 28.6 | 9 |
| sign, delta 0.03, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.52 short at 10% (dev1-ladder) | 0.000 / 0.000 | 0.001 / 0.874 | 0.138 / 0.976 | 3.5 / 16.1 | 2 |
| sign, delta 0.03, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.33 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.001 / 0.989 | 0.312 / 1.000 | 6.2 / 21.3 | 4 |
| sign, delta 0.03, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.072 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.002 / 1.000 | 0.568 / 1.000 | 10.7 / 29.0 | 7 |
| sign, delta 0.04, alpha 0.05, cap 40 | no | yes | no / no | yes | 0.000 / 0.002 | 0.036 / 1.000 | 0.964 / 1.000 | 17.0 / 26.9 | 12 |
| sign, delta 0.04, alpha 0.02, cap 30 | yes | yes | no / no | no: 0.032 short at 5% (dev2-ladder) | 0.000 / 0.001 | 0.015 / 0.993 | 0.833 / 1.000 | 11.4 / 21.1 | 8 |
| sign, delta 0.04, alpha 0.02, cap 40 | yes | yes | no / no | no: 0.029 short at 5% (dev2-ladder) | 0.000 / 0.001 | 0.015 / 0.999 | 0.923 / 1.000 | 15.6 / 27.6 | 11 |
| sign, delta 0.04, alpha 0.01, cap 20 | yes | yes | no / yes | no: 0.14 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.008 / 0.886 | 0.502 / 1.000 | 5.8 / 13.9 | 4 |
| sign, delta 0.04, alpha 0.01, cap 30 | yes | yes | no / no | no: 0.045 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.008 / 0.982 | 0.742 / 1.000 | 10.0 / 19.7 | 7 |
| sign, delta 0.04, alpha 0.01, cap 40 | yes | yes | no / no | no: 0.043 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.007 / 0.999 | 0.894 / 1.000 | 15.6 / 29.2 | 11 |
| sign, delta 0.04, alpha 0.005, cap 10 | yes | yes | no / yes | no: 0.53 short at 10% (dev2-ladder) | 0.000 / 0.000 | 0.004 / 0.401 | 0.144 / 0.828 | 1.7 / 6.5 | 1 |
| sign, delta 0.04, alpha 0.005, cap 20 | yes | yes | yes / yes | no: 0.28 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.004 / 0.774 | 0.362 / 0.996 | 4.6 / 12.7 | 3 |
| sign, delta 0.04, alpha 0.005, cap 30 | yes | yes | no / no | no: 0.052 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.004 / 0.975 | 0.688 / 1.000 | 10.0 / 20.3 | 7 |
| sign, delta 0.04, alpha 0.005, cap 40 | yes | yes | no / no | no: 0.051 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.004 / 0.996 | 0.830 / 1.000 | 14.2 / 28.0 | 10 |
| sign, delta 0.04, alpha 0.003, cap 10 | yes | yes | yes / yes | no: 0.56 short at 10% (dev2-ladder) | 0.000 / 0.000 | 0.002 / 0.358 | 0.116 / 0.821 | 1.7 / 6.9 | 1 |
| sign, delta 0.04, alpha 0.003, cap 20 | yes | yes | yes / yes | no: 0.31 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.002 / 0.751 | 0.329 / 0.996 | 4.6 / 13.4 | 3 |
| sign, delta 0.04, alpha 0.003, cap 30 | yes | yes | yes / yes | no: 0.065 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.002 / 0.946 | 0.576 / 1.000 | 8.6 / 20.0 | 6 |
| sign, delta 0.04, alpha 0.003, cap 40 | yes | yes | no / no | no: 0.054 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.002 / 0.995 | 0.804 / 1.000 | 14.2 / 28.7 | 10 |
| sign, delta 0.04, alpha 0.002, cap 10 | yes | yes | yes / yes | no: 0.56 short at 10% (dev2-ladder) | 0.000 / 0.000 | 0.002 / 0.358 | 0.116 / 0.821 | 1.7 / 6.9 | 1 |
| sign, delta 0.04, alpha 0.002, cap 20 | yes | yes | yes / yes | no: 0.36 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.001 / 0.711 | 0.279 / 0.995 | 4.6 / 14.7 | 3 |
| sign, delta 0.04, alpha 0.002, cap 30 | yes | yes | yes / yes | no: 0.096 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.002 / 0.938 | 0.545 / 1.000 | 8.6 / 20.4 | 6 |
| sign, delta 0.04, alpha 0.002, cap 40 | yes | yes | no / no | no: 0.057 short at 5% (dev2-ladder) | 0.000 / 0.000 | 0.001 / 0.988 | 0.731 / 1.000 | 12.8 / 26.4 | 9 |
| sign, delta 0.04, alpha 0.001, cap 20 | yes | yes | yes / yes | no: 0.39 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.001 / 0.684 | 0.249 / 0.994 | 4.6 / 15.2 | 3 |
| sign, delta 0.04, alpha 0.001, cap 30 | yes | yes | yes / yes | no: 0.14 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.001 / 0.926 | 0.502 / 1.000 | 8.6 / 21.9 | 6 |
| sign, delta 0.04, alpha 0.001, cap 40 | yes | yes | yes / yes | no: 0.06 short at 5% (dev1-ladder) | 0.000 / 0.000 | 0.001 / 0.984 | 0.679 / 1.000 | 12.8 / 26.9 | 9 |
| sign, delta 0.04, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.56 short at 10% (dev1-ladder) | 0.000 / 0.000 | 0.000 / 0.397 | 0.089 / 0.946 | 3.2 / 14.0 | 2 |
| sign, delta 0.04, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.43 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.000 / 0.696 | 0.208 / 0.998 | 5.8 / 21.2 | 4 |
| sign, delta 0.04, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.23 short at 10% (dev2-replay) | 0.000 / 0.000 | 0.000 / 0.914 | 0.412 / 1.000 | 10.0 / 28.7 | 7 |
| sign, delta 0.05, alpha 0.05, cap 40 | yes | yes | no / no | no: 0.062 short at 5% (dev2-replay-solo-lowload) | 0.000 / 0.000 | 0.004 / 0.040 | 0.810 / 1.000 | 16.2 / 24.5 | 12 |
| sign, delta 0.05, alpha 0.02, cap 20 | yes | yes | yes / yes | no: 0.23 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.002 / 0.015 | 0.341 / 0.999 | 5.7 / 8.6 | 4 |
| sign, delta 0.05, alpha 0.02, cap 30 | yes | yes | yes / yes | no: 0.07 short at 5% (dev2-replay-solo-lowload) | 0.000 / 0.000 | 0.001 / 0.017 | 0.569 / 1.000 | 10.9 / 16.6 | 8 |
| sign, delta 0.05, alpha 0.02, cap 40 | yes | yes | yes / yes | no: 0.07 short at 5% (dev2-replay-solo-lowload) | 0.000 / 0.000 | 0.001 / 0.017 | 0.698 / 1.000 | 14.9 / 22.7 | 11 |
| sign, delta 0.05, alpha 0.01, cap 10 | yes | yes | yes / yes | no: 0.58 short at 10% (dev2-ladder) | 0.000 / 0.000 | 0.001 / 0.007 | 0.095 / 0.814 | 1.7 / 2.7 | 1 |
| sign, delta 0.05, alpha 0.01, cap 20 | yes | yes | yes / yes | no: 0.3 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.001 / 0.008 | 0.270 / 0.998 | 5.7 / 8.6 | 4 |
| sign, delta 0.05, alpha 0.01, cap 30 | yes | yes | yes / yes | no: 0.12 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.009 | 0.448 / 1.000 | 9.5 / 14.7 | 7 |
| sign, delta 0.05, alpha 0.01, cap 40 | yes | yes | yes / yes | no: 0.073 short at 5% (dev2-replay-solo-lowload) | 0.000 / 0.000 | 0.000 / 0.009 | 0.621 / 1.000 | 14.9 / 22.8 | 11 |
| sign, delta 0.05, alpha 0.005, cap 10 | yes | yes | yes / yes | no: 0.6 short at 10% (dev2-ladder) | 0.000 / 0.000 | 0.001 / 0.003 | 0.079 / 0.785 | 1.7 / 2.7 | 1 |
| sign, delta 0.05, alpha 0.005, cap 20 | yes | yes | yes / yes | no: 0.39 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.004 | 0.179 / 0.988 | 4.5 / 6.6 | 3 |
| sign, delta 0.05, alpha 0.005, cap 30 | yes | yes | yes / yes | no: 0.19 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.004 | 0.379 / 1.000 | 9.5 / 14.7 | 7 |
| sign, delta 0.05, alpha 0.005, cap 40 | yes | yes | yes / yes | no: 0.074 short at 5% (dev2-replay-solo-lowload) | 0.000 / 0.000 | 0.000 / 0.005 | 0.516 / 1.000 | 13.5 / 20.9 | 10 |
| sign, delta 0.05, alpha 0.003, cap 10 | yes | yes | yes / yes | no: 0.62 short at 10% (dev2-ladder) | 0.000 / 0.000 | 0.000 / 0.002 | 0.052 / 0.757 | 1.7 / 2.7 | 1 |
| sign, delta 0.05, alpha 0.003, cap 20 | yes | yes | yes / yes | no: 0.42 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.003 | 0.149 / 0.986 | 4.5 / 6.6 | 3 |
| sign, delta 0.05, alpha 0.003, cap 30 | yes | yes | yes / yes | no: 0.29 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.002 | 0.281 / 1.000 | 8.2 / 12.7 | 6 |
| sign, delta 0.05, alpha 0.003, cap 40 | yes | yes | yes / yes | no: 0.1 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.003 | 0.466 / 1.000 | 13.5 / 20.9 | 10 |
| sign, delta 0.05, alpha 0.002, cap 10 | yes | yes | yes / yes | no: 0.62 short at 10% (dev2-ladder) | 0.000 / 0.000 | 0.000 / 0.002 | 0.052 / 0.757 | 1.7 / 2.7 | 1 |
| sign, delta 0.05, alpha 0.002, cap 20 | yes | yes | yes / yes | no: 0.47 short at 10% (dev1-ladder) | 0.000 / 0.000 | 0.000 / 0.001 | 0.118 / 0.982 | 4.5 / 6.6 | 3 |
| sign, delta 0.05, alpha 0.002, cap 30 | yes | yes | yes / yes | no: 0.31 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.002 | 0.257 / 1.000 | 8.2 / 12.7 | 6 |
| sign, delta 0.05, alpha 0.002, cap 40 | yes | yes | yes / yes | no: 0.19 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.002 | 0.383 / 1.000 | 12.2 / 18.8 | 9 |
| sign, delta 0.05, alpha 0.001, cap 20 | yes | yes | yes / yes | no: 0.5 short at 10% (dev1-ladder) | 0.000 / 0.000 | 0.000 / 0.001 | 0.095 / 0.980 | 4.5 / 6.6 | 3 |
| sign, delta 0.05, alpha 0.001, cap 30 | yes | yes | yes / yes | no: 0.36 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.001 | 0.214 / 1.000 | 8.2 / 12.7 | 6 |
| sign, delta 0.05, alpha 0.001, cap 40 | yes | yes | yes / yes | no: 0.25 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.001 | 0.320 / 1.000 | 12.2 / 18.9 | 9 |
| sign, delta 0.05, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.65 short at 10% (dev1-ladder) | 0.000 / 0.000 | 0.000 / 0.000 | 0.025 / 0.883 | 3.1 / 4.6 | 2 |
| sign, delta 0.05, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.56 short at 10% (dev1-ladder) | 0.000 / 0.000 | 0.000 / 0.000 | 0.058 / 0.992 | 5.7 / 8.6 | 4 |
| sign, delta 0.05, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.44 short at 10% (dev2-replay-solo) | 0.000 / 0.000 | 0.000 / 0.000 | 0.130 / 1.000 | 9.5 / 14.8 | 7 |

The cost of a round, per group: the mean over its rounds of every run but the preference's timed one (each configuration is settled and timed: twice its time; the A/A arm, a diagnostic, left out): dev2-replay 0.056 s; dev2-ladder 0.197 s; dev2-replay-solo 0.0422 s; dev2-ladder-lowload 0.129 s; dev2-replay-solo-lowload 0.0295 s; dev1-replay 0.0814 s; dev1-ladder 0.396 s; dev1-replay-solo 0.0582 s.

Per group, for every candidate that exists at alpha / m within its cap (false-switch rate, the current rule's, and both with the group's contest effect added):

| rule | dev2-replay | dev2-ladder | dev2-replay-solo | dev2-ladder-lowload | dev2-replay-solo-lowload | dev1-replay | dev1-ladder | dev1-replay-solo |
|---|---|---|---|---|---|---|---|---|
| delta 0, alpha 0.05, cap 10 | 0.052 vs 0.00091 (0.17 vs 0.044) | 0.053 vs 0.00047 (0.15 vs 0.018) | 0.02 vs 0.00027 (0.18 vs 0.057) | 0.048 vs 2.7e-05 (0.11 vs 0.00034) | 0.026 vs 6.4e-07 (0.026 vs 6.4e-07) | 0.055 vs 4.7e-11 (0.1 vs 1.8e-08) | 0.068 vs 0.0005 (0.068 vs 0.0005) | 0.055 vs <1e-12 (0.055 vs <1e-12) |
| delta 0, alpha 0.05, cap 20 | 0.063 vs 0.00091 (0.26 vs 0.044) | 0.059 vs 0.00047 (0.23 vs 0.018) | 0.014 vs 0.00027 (0.24 vs 0.057) | 0.04 vs 2.7e-05 (0.14 vs 0.00034) | 0.032 vs 6.4e-07 (0.032 vs 6.4e-07) | 0.06 vs 4.7e-11 (0.15 vs 1.8e-08) | 0.076 vs 0.0005 (0.076 vs 0.0005) | 0.048 vs <1e-12 (0.048 vs <1e-12) |
| delta 0, alpha 0.05, cap 30 | 0.061 vs 0.00091 (0.29 vs 0.044) | 0.056 vs 0.00047 (0.25 vs 0.018) | 0.012 vs 0.00027 (0.26 vs 0.057) | 0.034 vs 2.7e-05 (0.15 vs 0.00034) | 0.031 vs 6.4e-07 (0.031 vs 6.4e-07) | 0.056 vs 4.7e-11 (0.17 vs 1.8e-08) | 0.073 vs 0.0005 (0.073 vs 0.0005) | 0.042 vs <1e-12 (0.042 vs <1e-12) |
| delta 0, alpha 0.05, cap 40 | 0.065 vs 0.00091 (0.33 vs 0.044) | 0.059 vs 0.00047 (0.29 vs 0.018) | 0.007 vs 0.00027 (0.28 vs 0.057) | 0.03 vs 2.7e-05 (0.17 vs 0.00034) | 0.024 vs 6.4e-07 (0.024 vs 6.4e-07) | 0.06 vs 4.7e-11 (0.2 vs 1.8e-08) | 0.078 vs 0.0005 (0.078 vs 0.0005) | 0.037 vs <1e-12 (0.037 vs <1e-12) |
| delta 0, alpha 0.02, cap 10 | 0.021 vs 0.00091 (0.088 vs 0.044) | 0.02 vs 0.00047 (0.07 vs 0.018) | 0.0088 vs 0.00027 (0.11 vs 0.057) | 0.017 vs 2.7e-05 (0.051 vs 0.00034) | 0.016 vs 6.4e-07 (0.016 vs 6.4e-07) | 0.019 vs 4.7e-11 (0.042 vs 1.8e-08) | 0.026 vs 0.0005 (0.026 vs 0.0005) | 0.02 vs <1e-12 (0.02 vs <1e-12) |
| delta 0, alpha 0.02, cap 20 | 0.024 vs 0.00091 (0.18 vs 0.044) | 0.023 vs 0.00047 (0.16 vs 0.018) | 0.0038 vs 0.00027 (0.19 vs 0.057) | 0.015 vs 2.7e-05 (0.079 vs 0.00034) | 0.008 vs 6.4e-07 (0.008 vs 6.4e-07) | 0.024 vs 4.7e-11 (0.084 vs 1.8e-08) | 0.031 vs 0.0005 (0.031 vs 0.0005) | 0.018 vs <1e-12 (0.018 vs <1e-12) |
| delta 0, alpha 0.02, cap 30 | 0.027 vs 0.00091 (0.25 vs 0.044) | 0.024 vs 0.00047 (0.22 vs 0.018) | 0.0026 vs 0.00027 (0.23 vs 0.057) | 0.012 vs 2.7e-05 (0.1 vs 0.00034) | 0.0085 vs 6.4e-07 (0.0085 vs 6.4e-07) | 0.025 vs 4.7e-11 (0.12 vs 1.8e-08) | 0.033 vs 0.0005 (0.033 vs 0.0005) | 0.015 vs <1e-12 (0.015 vs <1e-12) |
| delta 0, alpha 0.02, cap 40 | 0.028 vs 0.00091 (0.28 vs 0.044) | 0.024 vs 0.00047 (0.24 vs 0.018) | 0.0022 vs 0.00027 (0.25 vs 0.057) | 0.011 vs 2.7e-05 (0.12 vs 0.00034) | 0.0084 vs 6.4e-07 (0.0084 vs 6.4e-07) | 0.025 vs 4.7e-11 (0.14 vs 1.8e-08) | 0.034 vs 0.0005 (0.034 vs 0.0005) | 0.013 vs <1e-12 (0.013 vs <1e-12) |
| delta 0, alpha 0.01, cap 10 | 0.0098 vs 0.00091 (0.066 vs 0.044) | 0.01 vs 0.00047 (0.053 vs 0.018) | 0.0025 vs 0.00027 (0.089 vs 0.057) | 0.008 vs 2.7e-05 (0.032 vs 0.00034) | 0.0036 vs 6.4e-07 (0.0036 vs 6.4e-07) | 0.01 vs 4.7e-11 (0.029 vs 1.8e-08) | 0.013 vs 0.0005 (0.013 vs 0.0005) | 0.0095 vs <1e-12 (0.0095 vs <1e-12) |
| delta 0, alpha 0.01, cap 20 | 0.013 vs 0.00091 (0.15 vs 0.044) | 0.012 vs 0.00047 (0.13 vs 0.018) | 0.0018 vs 0.00027 (0.17 vs 0.057) | 0.0067 vs 2.7e-05 (0.054 vs 0.00034) | 0.0046 vs 6.4e-07 (0.0046 vs 6.4e-07) | 0.012 vs 4.7e-11 (0.058 vs 1.8e-08) | 0.016 vs 0.0005 (0.016 vs 0.0005) | 0.0084 vs <1e-12 (0.0084 vs <1e-12) |
| delta 0, alpha 0.01, cap 30 | 0.014 vs 0.00091 (0.21 vs 0.044) | 0.012 vs 0.00047 (0.19 vs 0.018) | 0.00099 vs 0.00027 (0.2 vs 0.057) | 0.0056 vs 2.7e-05 (0.073 vs 0.00034) | 0.0034 vs 6.4e-07 (0.0034 vs 6.4e-07) | 0.013 vs 4.7e-11 (0.086 vs 1.8e-08) | 0.017 vs 0.0005 (0.017 vs 0.0005) | 0.0071 vs <1e-12 (0.0071 vs <1e-12) |
| delta 0, alpha 0.01, cap 40 | 0.014 vs 0.00091 (0.25 vs 0.044) | 0.012 vs 0.00047 (0.22 vs 0.018) | 0.00071 vs 0.00027 (0.23 vs 0.057) | 0.005 vs 2.7e-05 (0.09 vs 0.00034) | 0.0028 vs 6.4e-07 (0.0028 vs 6.4e-07) | 0.013 vs 4.7e-11 (0.11 vs 1.8e-08) | 0.018 vs 0.0005 (0.018 vs 0.0005) | 0.0064 vs <1e-12 (0.0064 vs <1e-12) |
| delta 0, alpha 0.005, cap 10 | 0.0055 vs 0.00091 (0.052 vs 0.044) | 0.0051 vs 0.00047 (0.042 vs 0.018) | 0.0013 vs 0.00027 (0.081 vs 0.057) | 0.0035 vs 2.7e-05 (0.021 vs 0.00034) | 0.0028 vs 6.4e-07 (0.0028 vs 6.4e-07) | 0.0049 vs 4.7e-11 (0.018 vs 1.8e-08) | 0.0068 vs 0.0005 (0.0068 vs 0.0005) | 0.0044 vs <1e-12 (0.0044 vs <1e-12) |
| delta 0, alpha 0.005, cap 20 | 0.0061 vs 0.00091 (0.11 vs 0.044) | 0.0057 vs 0.00047 (0.098 vs 0.018) | 0.00059 vs 0.00027 (0.14 vs 0.057) | 0.0032 vs 2.7e-05 (0.034 vs 0.00034) | 0.0015 vs 6.4e-07 (0.0015 vs 6.4e-07) | 0.0059 vs 4.7e-11 (0.036 vs 1.8e-08) | 0.008 vs 0.0005 (0.008 vs 0.0005) | 0.0039 vs <1e-12 (0.0039 vs <1e-12) |
| delta 0, alpha 0.005, cap 30 | 0.0068 vs 0.00091 (0.18 vs 0.044) | 0.0059 vs 0.00047 (0.16 vs 0.018) | 0.00035 vs 0.00027 (0.18 vs 0.057) | 0.0024 vs 2.7e-05 (0.054 vs 0.00034) | 0.0014 vs 6.4e-07 (0.0014 vs 6.4e-07) | 0.0061 vs 4.7e-11 (0.065 vs 1.8e-08) | 0.0086 vs 0.0005 (0.0086 vs 0.0005) | 0.0031 vs <1e-12 (0.0031 vs <1e-12) |
| delta 0, alpha 0.005, cap 40 | 0.0073 vs 0.00091 (0.22 vs 0.044) | 0.0062 vs 0.00047 (0.19 vs 0.018) | 0.00032 vs 0.00027 (0.2 vs 0.057) | 0.0023 vs 2.7e-05 (0.067 vs 0.00034) | 0.0014 vs 6.4e-07 (0.0014 vs 6.4e-07) | 0.0065 vs 4.7e-11 (0.083 vs 1.8e-08) | 0.0092 vs 0.0005 (0.0092 vs 0.0005) | 0.003 vs <1e-12 (0.003 vs <1e-12) |
| delta 0, alpha 0.003, cap 10 | 0.0025 vs 0.00091 (0.04 vs 0.044) | 0.0025 vs 0.00047 (0.033 vs 0.018) | 0.00036 vs 0.00027 (0.066 vs 0.057) | 0.0017 vs 2.7e-05 (0.013 vs 0.00034) | 0.00061 vs 6.4e-07 (0.00061 vs 6.4e-07) | 0.0027 vs 4.7e-11 (0.013 vs 1.8e-08) | 0.0036 vs 0.0005 (0.0036 vs 0.0005) | 0.0021 vs <1e-12 (0.0021 vs <1e-12) |
| delta 0, alpha 0.003, cap 20 | 0.0041 vs 0.00091 (0.099 vs 0.044) | 0.0038 vs 0.00047 (0.089 vs 0.018) | 0.00034 vs 0.00027 (0.13 vs 0.057) | 0.002 vs 2.7e-05 (0.028 vs 0.00034) | 0.00091 vs 6.4e-07 (0.00091 vs 6.4e-07) | 0.004 vs 4.7e-11 (0.03 vs 1.8e-08) | 0.0054 vs 0.0005 (0.0054 vs 0.0005) | 0.0025 vs <1e-12 (0.0025 vs <1e-12) |
| delta 0, alpha 0.003, cap 30 | 0.0035 vs 0.00091 (0.15 vs 0.044) | 0.0031 vs 0.00047 (0.14 vs 0.018) | 0.00012 vs 0.00027 (0.16 vs 0.057) | 0.0012 vs 2.7e-05 (0.038 vs 0.00034) | 0.00052 vs 6.4e-07 (0.00052 vs 6.4e-07) | 0.0033 vs 4.7e-11 (0.046 vs 1.8e-08) | 0.0046 vs 0.0005 (0.0046 vs 0.0005) | 0.0015 vs <1e-12 (0.0015 vs <1e-12) |
| delta 0, alpha 0.003, cap 40 | 0.0044 vs 0.00091 (0.2 vs 0.044) | 0.0038 vs 0.00047 (0.18 vs 0.018) | 0.00012 vs 0.00027 (0.19 vs 0.057) | 0.0013 vs 2.7e-05 (0.056 vs 0.00034) | 0.00057 vs 6.4e-07 (0.00057 vs 6.4e-07) | 0.004 vs 4.7e-11 (0.071 vs 1.8e-08) | 0.0057 vs 0.0005 (0.0057 vs 0.0005) | 0.0017 vs <1e-12 (0.0017 vs <1e-12) |
| delta 0, alpha 0.002, cap 10 | 0.0025 vs 0.00091 (0.04 vs 0.044) | 0.0025 vs 0.00047 (0.033 vs 0.018) | 0.00036 vs 0.00027 (0.066 vs 0.057) | 0.0017 vs 2.7e-05 (0.013 vs 0.00034) | 0.00061 vs 6.4e-07 (0.00061 vs 6.4e-07) | 0.0027 vs 4.7e-11 (0.013 vs 1.8e-08) | 0.0036 vs 0.0005 (0.0036 vs 0.0005) | 0.0021 vs <1e-12 (0.0021 vs <1e-12) |
| delta 0, alpha 0.002, cap 20 | 0.0018 vs 0.00091 (0.081 vs 0.044) | 0.0017 vs 0.00047 (0.075 vs 0.018) | 9.5e-05 vs 0.00027 (0.12 vs 0.057) | 0.00075 vs 2.7e-05 (0.019 vs 0.00034) | 0.00031 vs 6.4e-07 (0.00031 vs 6.4e-07) | 0.0017 vs 4.7e-11 (0.02 vs 1.8e-08) | 0.0024 vs 0.0005 (0.0024 vs 0.0005) | 0.00097 vs <1e-12 (0.00097 vs <1e-12) |
| delta 0, alpha 0.002, cap 30 | 0.0028 vs 0.00091 (0.14 vs 0.044) | 0.0025 vs 0.00047 (0.13 vs 0.018) | 0.00011 vs 0.00027 (0.16 vs 0.057) | 0.00096 vs 2.7e-05 (0.034 vs 0.00034) | 0.00043 vs 6.4e-07 (0.00043 vs 6.4e-07) | 0.0026 vs 4.7e-11 (0.04 vs 1.8e-08) | 0.0037 vs 0.0005 (0.0037 vs 0.0005) | 0.0013 vs <1e-12 (0.0013 vs <1e-12) |
| delta 0, alpha 0.002, cap 40 | 0.0029 vs 0.00091 (0.18 vs 0.044) | 0.0025 vs 0.00047 (0.16 vs 0.018) | 9.1e-05 vs 0.00027 (0.18 vs 0.057) | 0.0009 vs 2.7e-05 (0.044 vs 0.00034) | 0.00036 vs 6.4e-07 (0.00036 vs 6.4e-07) | 0.0027 vs 4.7e-11 (0.056 vs 1.8e-08) | 0.0039 vs 0.0005 (0.0039 vs 0.0005) | 0.0012 vs <1e-12 (0.0012 vs <1e-12) |
| delta 0, alpha 0.001, cap 20 | 0.0013 vs 0.00091 (0.072 vs 0.044) | 0.0012 vs 0.00047 (0.067 vs 0.018) | 6.9e-05 vs 0.00027 (0.11 vs 0.057) | 0.00055 vs 2.7e-05 (0.015 vs 0.00034) | 0.00018 vs 6.4e-07 (0.00018 vs 6.4e-07) | 0.0012 vs 4.7e-11 (0.017 vs 1.8e-08) | 0.0018 vs 0.0005 (0.0018 vs 0.0005) | 0.0007 vs <1e-12 (0.0007 vs <1e-12) |
| delta 0, alpha 0.001, cap 30 | 0.0015 vs 0.00091 (0.13 vs 0.044) | 0.0013 vs 0.00047 (0.12 vs 0.018) | 4.7e-05 vs 0.00027 (0.15 vs 0.057) | 0.00043 vs 2.7e-05 (0.026 vs 0.00034) | 0.00021 vs 6.4e-07 (0.00021 vs 6.4e-07) | 0.0013 vs 4.7e-11 (0.032 vs 1.8e-08) | 0.0019 vs 0.0005 (0.0019 vs 0.0005) | 0.00058 vs <1e-12 (0.00058 vs <1e-12) |
| delta 0, alpha 0.001, cap 40 | 0.0015 vs 0.00091 (0.16 vs 0.044) | 0.0013 vs 0.00047 (0.15 vs 0.018) | 4.4e-05 vs 0.00027 (0.17 vs 0.057) | 0.0004 vs 2.7e-05 (0.034 vs 0.00034) | 0.0002 vs 6.4e-07 (0.0002 vs 6.4e-07) | 0.0013 vs 4.7e-11 (0.044 vs 1.8e-08) | 0.002 vs 0.0005 (0.002 vs 0.0005) | 0.00055 vs <1e-12 (0.00055 vs <1e-12) |
| delta 0, alpha 0.0001, cap 20 | 0.00014 vs 0.00091 (0.027 vs 0.044) | 0.00012 vs 0.00047 (0.028 vs 0.018) | 4.4e-06 vs 0.00027 (0.071 vs 0.057) | 4.4e-05 vs 2.7e-05 (0.0042 vs 0.00034) | 1.6e-05 vs 6.4e-07 (1.6e-05 vs 6.4e-07) | 0.00012 vs 4.7e-11 (0.0041 vs 1.8e-08) | 0.00018 vs 0.0005 (0.00018 vs 0.0005) | 6e-05 vs <1e-12 (6e-05 vs <1e-12) |
| delta 0, alpha 0.0001, cap 30 | 0.00015 vs 0.00091 (0.056 vs 0.044) | 0.00013 vs 0.00047 (0.058 vs 0.018) | 2e-06 vs 0.00027 (0.11 vs 0.057) | 3.8e-05 vs 2.7e-05 (0.0076 vs 0.00034) | 7.8e-06 vs 6.4e-07 (7.8e-06 vs 6.4e-07) | 0.00014 vs 4.7e-11 (0.0089 vs 1.8e-08) | 0.00021 vs 0.0005 (0.00021 vs 0.0005) | 5.2e-05 vs <1e-12 (5.2e-05 vs <1e-12) |
| delta 0, alpha 0.0001, cap 40 | 0.00015 vs 0.00091 (0.097 vs 0.044) | 0.00012 vs 0.00047 (0.094 vs 0.018) | 1.2e-06 vs 0.00027 (0.13 vs 0.057) | 2.5e-05 vs 2.7e-05 (0.013 vs 0.00034) | 8e-06 vs 6.4e-07 (8e-06 vs 6.4e-07) | 0.00012 vs 4.7e-11 (0.017 vs 1.8e-08) | 0.0002 vs 0.0005 (0.0002 vs 0.0005) | 3.6e-05 vs <1e-12 (3.6e-05 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 10 | 0.024 vs 0.00091 (0.13 vs 0.044) | 0.02 vs 0.00047 (0.093 vs 0.018) | 0.012 vs 0.00027 (0.16 vs 0.057) | 0.015 vs 2.7e-05 (0.05 vs 0.00034) | 0.0012 vs 6.4e-07 (0.0012 vs 6.4e-07) | 0.0052 vs 4.7e-11 (0.018 vs 1.8e-08) | 0.018 vs 0.0005 (0.018 vs 0.0005) | 2.1e-06 vs <1e-12 (2.1e-06 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 20 | 0.022 vs 0.00091 (0.19 vs 0.044) | 0.016 vs 0.00047 (0.14 vs 0.018) | 0.0062 vs 0.00027 (0.21 vs 0.057) | 0.01 vs 2.7e-05 (0.059 vs 0.00034) | 0.00048 vs 6.4e-07 (0.00048 vs 6.4e-07) | 0.0025 vs 4.7e-11 (0.019 vs 1.8e-08) | 0.016 vs 0.0005 (0.016 vs 0.0005) | 1.6e-07 vs <1e-12 (1.6e-07 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 30 | 0.019 vs 0.00091 (0.22 vs 0.044) | 0.014 vs 0.00047 (0.16 vs 0.018) | 0.0052 vs 0.00027 (0.23 vs 0.057) | 0.0081 vs 2.7e-05 (0.062 vs 0.00034) | 0.00044 vs 6.4e-07 (0.00044 vs 6.4e-07) | 0.0019 vs 4.7e-11 (0.019 vs 1.8e-08) | 0.014 vs 0.0005 (0.014 vs 0.0005) | 1.5e-07 vs <1e-12 (1.5e-07 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 40 | 0.017 vs 0.00091 (0.25 vs 0.044) | 0.01 vs 0.00047 (0.17 vs 0.018) | 0.0024 vs 0.00027 (0.25 vs 0.057) | 0.0056 vs 2.7e-05 (0.071 vs 0.00034) | 8.5e-05 vs 6.4e-07 (8.5e-05 vs 6.4e-07) | 0.001 vs 4.7e-11 (0.022 vs 1.8e-08) | 0.012 vs 0.0005 (0.012 vs 0.0005) | 1.1e-08 vs <1e-12 (1.1e-08 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 10 | 0.0091 vs 0.00091 (0.063 vs 0.044) | 0.0076 vs 0.00047 (0.043 vs 0.018) | 0.0042 vs 0.00027 (0.093 vs 0.057) | 0.005 vs 2.7e-05 (0.021 vs 0.00034) | 0.00041 vs 6.4e-07 (0.00041 vs 6.4e-07) | 0.0014 vs 4.7e-11 (0.0061 vs 1.8e-08) | 0.0061 vs 0.0005 (0.0061 vs 0.0005) | 1.5e-07 vs <1e-12 (1.5e-07 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 20 | 0.0074 vs 0.00091 (0.13 vs 0.044) | 0.0053 vs 0.00047 (0.097 vs 0.018) | 0.0015 vs 0.00027 (0.16 vs 0.057) | 0.0032 vs 2.7e-05 (0.03 vs 0.00034) | 5.9e-05 vs 6.4e-07 (5.9e-05 vs 6.4e-07) | 0.00069 vs 4.7e-11 (0.0086 vs 1.8e-08) | 0.0055 vs 0.0005 (0.0055 vs 0.0005) | 1.1e-08 vs <1e-12 (1.1e-08 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 30 | 0.0064 vs 0.00091 (0.18 vs 0.044) | 0.004 vs 0.00047 (0.13 vs 0.018) | 0.0008 vs 0.00027 (0.2 vs 0.057) | 0.002 vs 2.7e-05 (0.039 vs 0.00034) | 2.3e-05 vs 6.4e-07 (2.3e-05 vs 6.4e-07) | 0.00032 vs 4.7e-11 (0.011 vs 1.8e-08) | 0.0046 vs 0.0005 (0.0046 vs 0.0005) | 8.1e-10 vs <1e-12 (8.1e-10 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 40 | 0.0057 vs 0.00091 (0.2 vs 0.044) | 0.0033 vs 0.00047 (0.14 vs 0.018) | 0.00065 vs 0.00027 (0.22 vs 0.057) | 0.0016 vs 2.7e-05 (0.044 vs 0.00034) | 2.1e-05 vs 6.4e-07 (2.1e-05 vs 6.4e-07) | 0.00024 vs 4.7e-11 (0.012 vs 1.8e-08) | 0.004 vs 0.0005 (0.004 vs 0.0005) | 7.8e-10 vs <1e-12 (7.8e-10 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 10 | 0.0037 vs 0.00091 (0.046 vs 0.044) | 0.003 vs 0.00047 (0.032 vs 0.018) | 0.0012 vs 0.00027 (0.071 vs 0.057) | 0.002 vs 2.7e-05 (0.012 vs 0.00034) | 5.4e-05 vs 6.4e-07 (5.4e-05 vs 6.4e-07) | 0.00052 vs 4.7e-11 (0.0035 vs 1.8e-08) | 0.0028 vs 0.0005 (0.0028 vs 0.0005) | 1.1e-08 vs <1e-12 (1.1e-08 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 20 | 0.0035 vs 0.00091 (0.11 vs 0.044) | 0.0024 vs 0.00047 (0.08 vs 0.018) | 0.00061 vs 0.00027 (0.14 vs 0.057) | 0.0013 vs 2.7e-05 (0.019 vs 0.00034) | 2.1e-05 vs 6.4e-07 (2.1e-05 vs 6.4e-07) | 0.00022 vs 4.7e-11 (0.0049 vs 1.8e-08) | 0.0024 vs 0.0005 (0.0024 vs 0.0005) | 7.8e-10 vs <1e-12 (7.8e-10 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 30 | 0.0029 vs 0.00091 (0.15 vs 0.044) | 0.0017 vs 0.00047 (0.11 vs 0.018) | 0.00027 vs 0.00027 (0.17 vs 0.057) | 0.00081 vs 2.7e-05 (0.025 vs 0.00034) | 4.2e-06 vs 6.4e-07 (4.2e-06 vs 6.4e-07) | 0.00011 vs 4.7e-11 (0.0065 vs 1.8e-08) | 0.002 vs 0.0005 (0.002 vs 0.0005) | 5.8e-11 vs <1e-12 (5.8e-11 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 40 | 0.0025 vs 0.00091 (0.18 vs 0.044) | 0.0014 vs 0.00047 (0.13 vs 0.018) | 0.0002 vs 0.00027 (0.2 vs 0.057) | 0.00064 vs 2.7e-05 (0.031 vs 0.00034) | 2.8e-06 vs 6.4e-07 (2.8e-06 vs 6.4e-07) | 8.9e-05 vs 4.7e-11 (0.0081 vs 1.8e-08) | 0.0018 vs 0.0005 (0.0018 vs 0.0005) | 5.6e-11 vs <1e-12 (5.6e-11 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 10 | 0.0018 vs 0.00091 (0.035 vs 0.044) | 0.0014 vs 0.00047 (0.024 vs 0.018) | 0.00047 vs 0.00027 (0.062 vs 0.057) | 0.00079 vs 2.7e-05 (0.0073 vs 0.00034) | 1.9e-05 vs 6.4e-07 (1.9e-05 vs 6.4e-07) | 0.00016 vs 4.7e-11 (0.0017 vs 1.8e-08) | 0.0012 vs 0.0005 (0.0012 vs 0.0005) | 7.8e-10 vs <1e-12 (7.8e-10 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 20 | 0.0015 vs 0.00091 (0.075 vs 0.044) | 0.00097 vs 0.00047 (0.058 vs 0.018) | 0.00018 vs 0.00027 (0.11 vs 0.057) | 0.00051 vs 2.7e-05 (0.011 vs 0.00034) | 2.8e-06 vs 6.4e-07 (2.8e-06 vs 6.4e-07) | 8.1e-05 vs 4.7e-11 (0.0027 vs 1.8e-08) | 0.0011 vs 0.0005 (0.0011 vs 0.0005) | 5.6e-11 vs <1e-12 (5.6e-11 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 30 | 0.0012 vs 0.00091 (0.13 vs 0.044) | 0.00065 vs 0.00047 (0.096 vs 0.018) | 8e-05 vs 0.00027 (0.16 vs 0.057) | 0.00028 vs 2.7e-05 (0.017 vs 0.00034) | 1e-06 vs 6.4e-07 (1e-06 vs 6.4e-07) | 3e-05 vs 4.7e-11 (0.0042 vs 1.8e-08) | 0.00082 vs 0.0005 (0.00082 vs 0.0005) | 4e-12 vs <1e-12 (4e-12 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 40 | 0.0011 vs 0.00091 (0.15 vs 0.044) | 0.00061 vs 0.00047 (0.11 vs 0.018) | 7.6e-05 vs 0.00027 (0.18 vs 0.057) | 0.00025 vs 2.7e-05 (0.021 vs 0.00034) | 9.9e-07 vs 6.4e-07 (9.9e-07 vs 6.4e-07) | 2.8e-05 vs 4.7e-11 (0.0052 vs 1.8e-08) | 0.00078 vs 0.0005 (0.00078 vs 0.0005) | 4e-12 vs <1e-12 (4e-12 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 10 | 0.00075 vs 0.00091 (0.027 vs 0.044) | 0.00054 vs 0.00047 (0.019 vs 0.018) | 0.00013 vs 0.00027 (0.05 vs 0.057) | 0.00031 vs 2.7e-05 (0.0045 vs 0.00034) | 2.5e-06 vs 6.4e-07 (2.5e-06 vs 6.4e-07) | 5.9e-05 vs 4.7e-11 (0.0011 vs 1.8e-08) | 0.00055 vs 0.0005 (0.00055 vs 0.0005) | 5.6e-11 vs <1e-12 (5.6e-11 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 20 | 0.00093 vs 0.00091 (0.067 vs 0.044) | 0.00058 vs 0.00047 (0.052 vs 0.018) | 9.1e-05 vs 0.00027 (0.1 vs 0.057) | 0.00028 vs 2.7e-05 (0.0088 vs 0.00034) | 1.1e-06 vs 6.4e-07 (1.1e-06 vs 6.4e-07) | 3.7e-05 vs 4.7e-11 (0.002 vs 1.8e-08) | 0.00066 vs 0.0005 (0.00066 vs 0.0005) | 4.2e-12 vs <1e-12 (4.2e-12 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 30 | 0.00055 vs 0.00091 (0.1 vs 0.044) | 0.00029 vs 0.00047 (0.081 vs 0.018) | 2.5e-05 vs 0.00027 (0.14 vs 0.057) | 0.00012 vs 2.7e-05 (0.011 vs 0.00034) | 1.4e-07 vs 6.4e-07 (1.4e-07 vs 6.4e-07) | 1.1e-05 vs 4.7e-11 (0.0026 vs 1.8e-08) | 0.00039 vs 0.0005 (0.00039 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 40 | 0.00058 vs 0.00091 (0.14 vs 0.044) | 0.00029 vs 0.00047 (0.11 vs 0.018) | 2.4e-05 vs 0.00027 (0.17 vs 0.057) | 0.00011 vs 2.7e-05 (0.017 vs 0.00034) | 1.4e-07 vs 6.4e-07 (1.4e-07 vs 6.4e-07) | 1.1e-05 vs 4.7e-11 (0.0041 vs 1.8e-08) | 0.00041 vs 0.0005 (0.00041 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 10 | 0.00075 vs 0.00091 (0.027 vs 0.044) | 0.00054 vs 0.00047 (0.019 vs 0.018) | 0.00013 vs 0.00027 (0.05 vs 0.057) | 0.00031 vs 2.7e-05 (0.0045 vs 0.00034) | 2.5e-06 vs 6.4e-07 (2.5e-06 vs 6.4e-07) | 5.9e-05 vs 4.7e-11 (0.0011 vs 1.8e-08) | 0.00055 vs 0.0005 (0.00055 vs 0.0005) | 5.6e-11 vs <1e-12 (5.6e-11 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 20 | 0.00035 vs 0.00091 (0.054 vs 0.044) | 0.0002 vs 0.00047 (0.043 vs 0.018) | 2.2e-05 vs 0.00027 (0.092 vs 0.057) | 8.8e-05 vs 2.7e-05 (0.0054 vs 0.00034) | 1.4e-07 vs 6.4e-07 (1.4e-07 vs 6.4e-07) | 9.8e-06 vs 4.7e-11 (0.0011 vs 1.8e-08) | 0.00024 vs 0.0005 (0.00024 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 30 | 0.00045 vs 0.00091 (0.096 vs 0.044) | 0.00024 vs 0.00047 (0.076 vs 0.018) | 2.3e-05 vs 0.00027 (0.13 vs 0.057) | 0.0001 vs 2.7e-05 (0.0098 vs 0.00034) | 1.4e-07 vs 6.4e-07 (1.4e-07 vs 6.4e-07) | 1e-05 vs 4.7e-11 (0.0022 vs 1.8e-08) | 0.00031 vs 0.0005 (0.00031 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 40 | 0.00041 vs 0.00091 (0.12 vs 0.044) | 0.00021 vs 0.00047 (0.095 vs 0.018) | 2.1e-05 vs 0.00027 (0.15 vs 0.057) | 8.9e-05 vs 2.7e-05 (0.013 vs 0.00034) | 1.3e-07 vs 6.4e-07 (1.3e-07 vs 6.4e-07) | 9.5e-06 vs 4.7e-11 (0.003 vs 1.8e-08) | 0.00029 vs 0.0005 (0.00029 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 20 | 0.00024 vs 0.00091 (0.047 vs 0.044) | 0.00014 vs 0.00047 (0.039 vs 0.018) | 1.8e-05 vs 0.00027 (0.084 vs 0.057) | 6.5e-05 vs 2.7e-05 (0.0043 vs 0.00034) | 1.2e-07 vs 6.4e-07 (1.2e-07 vs 6.4e-07) | 7.8e-06 vs 4.7e-11 (0.0009 vs 1.8e-08) | 0.00017 vs 0.0005 (0.00017 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 30 | 0.0002 vs 0.00091 (0.085 vs 0.044) | 0.0001 vs 0.00047 (0.069 vs 0.018) | 8.6e-06 vs 0.00027 (0.12 vs 0.057) | 3.8e-05 vs 2.7e-05 (0.0071 vs 0.00034) | 4.7e-08 vs 6.4e-07 (4.7e-08 vs 6.4e-07) | 3.1e-06 vs 4.7e-11 (0.0015 vs 1.8e-08) | 0.00013 vs 0.0005 (0.00013 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 40 | 0.00019 vs 0.00091 (0.11 vs 0.044) | 9.5e-05 vs 0.00047 (0.086 vs 0.018) | 8.3e-06 vs 0.00027 (0.14 vs 0.057) | 3.5e-05 vs 2.7e-05 (0.0091 vs 0.00034) | 4.6e-08 vs 6.4e-07 (4.6e-08 vs 6.4e-07) | 3e-06 vs 4.7e-11 (0.002 vs 1.8e-08) | 0.00012 vs 0.0005 (0.00012 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.0001, cap 20 | 2e-05 vs 0.00091 (0.017 vs 0.044) | 1e-05 vs 0.00047 (0.015 vs 0.018) | 7.4e-07 vs 0.00027 (0.048 vs 0.057) | 3.7e-06 vs 2.7e-05 (0.0009 vs 0.00034) | 2e-09 vs 6.4e-07 (2e-09 vs 6.4e-07) | 2.7e-07 vs 4.7e-11 (0.00015 vs 1.8e-08) | 1.3e-05 vs 0.0005 (1.3e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.0001, cap 30 | 1.5e-05 vs 0.00091 (0.036 vs 0.044) | 6.9e-06 vs 0.00047 (0.033 vs 0.018) | 2.8e-07 vs 0.00027 (0.075 vs 0.057) | 2.3e-06 vs 2.7e-05 (0.0016 vs 0.00034) | 2.9e-10 vs 6.4e-07 (2.9e-10 vs 6.4e-07) | 1.3e-07 vs 4.7e-11 (0.0003 vs 1.8e-08) | 1.1e-05 vs 0.0005 (1.1e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.0001, cap 40 | 1.1e-05 vs 0.00091 (0.063 vs 0.044) | 4.2e-06 vs 0.00047 (0.056 vs 0.018) | 1.2e-07 vs 0.00027 (0.1 vs 0.057) | 1.1e-06 vs 2.7e-05 (0.0028 vs 0.00034) | 1e-10 vs 6.4e-07 (1e-10 vs 6.4e-07) | 4.5e-08 vs 4.7e-11 (0.00053 vs 1.8e-08) | 6.9e-06 vs 0.0005 (6.9e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 10 | 0.017 vs 0.00091 (0.11 vs 0.044) | 0.0097 vs 0.00047 (0.078 vs 0.018) | 0.0096 vs 0.00027 (0.14 vs 0.057) | 0.0056 vs 2.7e-05 (0.028 vs 0.00034) | 0.00051 vs 6.4e-07 (0.00051 vs 6.4e-07) | 0.0011 vs 4.7e-11 (0.0059 vs 1.8e-08) | 0.0081 vs 0.0005 (0.0081 vs 0.0005) | 4.9e-08 vs <1e-12 (4.9e-08 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 20 | 0.014 vs 0.00091 (0.16 vs 0.044) | 0.0066 vs 0.00047 (0.12 vs 0.018) | 0.0047 vs 0.00027 (0.19 vs 0.057) | 0.0028 vs 2.7e-05 (0.031 vs 0.00034) | 9.7e-05 vs 6.4e-07 (9.7e-05 vs 6.4e-07) | 0.00035 vs 4.7e-11 (0.005 vs 1.8e-08) | 0.0058 vs 0.0005 (0.0058 vs 0.0005) | 1.8e-09 vs <1e-12 (1.8e-09 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 30 | 0.012 vs 0.00091 (0.18 vs 0.044) | 0.0054 vs 0.00047 (0.13 vs 0.018) | 0.0039 vs 0.00027 (0.21 vs 0.057) | 0.0022 vs 2.7e-05 (0.031 vs 0.00034) | 9.1e-05 vs 6.4e-07 (9.1e-05 vs 6.4e-07) | 0.00028 vs 4.7e-11 (0.0047 vs 1.8e-08) | 0.0045 vs 0.0005 (0.0045 vs 0.0005) | 1.7e-09 vs <1e-12 (1.7e-09 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 40 | 0.0089 vs 0.00091 (0.21 vs 0.044) | 0.0034 vs 0.00047 (0.15 vs 0.018) | 0.0017 vs 0.00027 (0.22 vs 0.057) | 0.0011 vs 2.7e-05 (0.035 vs 0.00034) | 1.3e-05 vs 6.4e-07 (1.3e-05 vs 6.4e-07) | 0.0001 vs 4.7e-11 (0.0048 vs 1.8e-08) | 0.0033 vs 0.0005 (0.0033 vs 0.0005) | 6.3e-11 vs <1e-12 (6.3e-11 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 10 | 0.0062 vs 0.00091 (0.053 vs 0.044) | 0.0035 vs 0.00047 (0.035 vs 0.018) | 0.0032 vs 0.00027 (0.08 vs 0.057) | 0.0016 vs 2.7e-05 (0.011 vs 0.00034) | 8.9e-05 vs 6.4e-07 (8.9e-05 vs 6.4e-07) | 0.00025 vs 4.7e-11 (0.0019 vs 1.8e-08) | 0.0026 vs 0.0005 (0.0026 vs 0.0005) | 1.7e-09 vs <1e-12 (1.7e-09 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 20 | 0.0043 vs 0.00091 (0.11 vs 0.044) | 0.0019 vs 0.00047 (0.079 vs 0.018) | 0.0012 vs 0.00027 (0.14 vs 0.057) | 0.00073 vs 2.7e-05 (0.015 vs 0.00034) | 1.2e-05 vs 6.4e-07 (1.2e-05 vs 6.4e-07) | 7.9e-05 vs 4.7e-11 (0.002 vs 1.8e-08) | 0.0017 vs 0.0005 (0.0017 vs 0.0005) | 6.2e-11 vs <1e-12 (6.2e-11 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 30 | 0.0033 vs 0.00091 (0.15 vs 0.044) | 0.0012 vs 0.00047 (0.11 vs 0.018) | 0.00056 vs 0.00027 (0.18 vs 0.057) | 0.00035 vs 2.7e-05 (0.018 vs 0.00034) | 2.3e-06 vs 6.4e-07 (2.3e-06 vs 6.4e-07) | 2.5e-05 vs 4.7e-11 (0.0021 vs 1.8e-08) | 0.0011 vs 0.0005 (0.0011 vs 0.0005) | 2.3e-12 vs <1e-12 (2.3e-12 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 40 | 0.0028 vs 0.00091 (0.17 vs 0.044) | 0.00096 vs 0.00047 (0.12 vs 0.018) | 0.00045 vs 0.00027 (0.2 vs 0.057) | 0.00027 vs 2.7e-05 (0.02 vs 0.00034) | 2.1e-06 vs 6.4e-07 (2.1e-06 vs 6.4e-07) | 1.9e-05 vs 4.7e-11 (0.0023 vs 1.8e-08) | 0.0009 vs 0.0005 (0.0009 vs 0.0005) | 2.2e-12 vs <1e-12 (2.2e-12 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 10 | 0.0024 vs 0.00091 (0.038 vs 0.044) | 0.0012 vs 0.00047 (0.025 vs 0.018) | 0.00091 vs 0.00027 (0.06 vs 0.057) | 0.00055 vs 2.7e-05 (0.0063 vs 0.00034) | 1.2e-05 vs 6.4e-07 (1.2e-05 vs 6.4e-07) | 6.9e-05 vs 4.7e-11 (0.00094 vs 1.8e-08) | 0.001 vs 0.0005 (0.001 vs 0.0005) | 6.2e-11 vs <1e-12 (6.2e-11 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 20 | 0.002 vs 0.00091 (0.087 vs 0.044) | 0.00078 vs 0.00047 (0.063 vs 0.018) | 0.00043 vs 0.00027 (0.12 vs 0.057) | 0.00025 vs 2.7e-05 (0.009 vs 0.00034) | 2.1e-06 vs 6.4e-07 (2.1e-06 vs 6.4e-07) | 1.9e-05 vs 4.7e-11 (0.001 vs 1.8e-08) | 0.00068 vs 0.0005 (0.00068 vs 0.0005) | 2.2e-12 vs <1e-12 (2.2e-12 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 30 | 0.0014 vs 0.00091 (0.12 vs 0.044) | 0.00046 vs 0.00047 (0.089 vs 0.018) | 0.00018 vs 0.00027 (0.16 vs 0.057) | 0.00012 vs 2.7e-05 (0.012 vs 0.00034) | 3.2e-07 vs 6.4e-07 (3.2e-07 vs 6.4e-07) | 6.8e-06 vs 4.7e-11 (0.0012 vs 1.8e-08) | 0.00045 vs 0.0005 (0.00045 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 40 | 0.0011 vs 0.00091 (0.15 vs 0.044) | 0.00034 vs 0.00047 (0.11 vs 0.018) | 0.00013 vs 0.00027 (0.18 vs 0.057) | 9.2e-05 vs 2.7e-05 (0.014 vs 0.00034) | 2.8e-07 vs 6.4e-07 (2.8e-07 vs 6.4e-07) | 5.4e-06 vs 4.7e-11 (0.0014 vs 1.8e-08) | 0.00036 vs 0.0005 (0.00036 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 10 | 0.0011 vs 0.00091 (0.029 vs 0.044) | 0.00052 vs 0.00047 (0.019 vs 0.018) | 0.00034 vs 0.00027 (0.052 vs 0.057) | 0.00018 vs 2.7e-05 (0.0035 vs 0.00034) | 2.1e-06 vs 6.4e-07 (2.1e-06 vs 6.4e-07) | 1.6e-05 vs 4.7e-11 (0.00042 vs 1.8e-08) | 0.0004 vs 0.0005 (0.0004 vs 0.0005) | 2.2e-12 vs <1e-12 (2.2e-12 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 20 | 0.00079 vs 0.00091 (0.061 vs 0.044) | 0.00028 vs 0.00047 (0.044 vs 0.018) | 0.00013 vs 0.00027 (0.095 vs 0.057) | 8.4e-05 vs 2.7e-05 (0.0052 vs 0.00034) | 2.8e-07 vs 6.4e-07 (2.8e-07 vs 6.4e-07) | 5.4e-06 vs 4.7e-11 (0.00052 vs 1.8e-08) | 0.00027 vs 0.0005 (0.00027 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 30 | 0.00054 vs 0.00091 (0.11 vs 0.044) | 0.00015 vs 0.00047 (0.077 vs 0.018) | 5.1e-05 vs 0.00027 (0.14 vs 0.057) | 3.3e-05 vs 2.7e-05 (0.0077 vs 0.00034) | 5e-08 vs 6.4e-07 (5e-08 vs 6.4e-07) | 1.3e-06 vs 4.7e-11 (0.00067 vs 1.8e-08) | 0.00015 vs 0.0005 (0.00015 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 40 | 0.0005 vs 0.00091 (0.13 vs 0.044) | 0.00014 vs 0.00047 (0.092 vs 0.018) | 4.9e-05 vs 0.00027 (0.16 vs 0.057) | 3.1e-05 vs 2.7e-05 (0.0094 vs 0.00034) | 5e-08 vs 6.4e-07 (5e-08 vs 6.4e-07) | 1.3e-06 vs 4.7e-11 (0.00081 vs 1.8e-08) | 0.00014 vs 0.0005 (0.00014 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 10 | 0.00043 vs 0.00091 (0.021 vs 0.044) | 0.00017 vs 0.00047 (0.014 vs 0.018) | 9.5e-05 vs 0.00027 (0.041 vs 0.057) | 6.1e-05 vs 2.7e-05 (0.0021 vs 0.00034) | 2.7e-07 vs 6.4e-07 (2.7e-07 vs 6.4e-07) | 4.6e-06 vs 4.7e-11 (0.00023 vs 1.8e-08) | 0.00016 vs 0.0005 (0.00016 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 20 | 0.00047 vs 0.00091 (0.054 vs 0.044) | 0.00015 vs 0.00047 (0.039 vs 0.018) | 6e-05 vs 0.00027 (0.087 vs 0.057) | 3.9e-05 vs 2.7e-05 (0.0039 vs 0.00034) | 5.6e-08 vs 6.4e-07 (5.6e-08 vs 6.4e-07) | 1.8e-06 vs 4.7e-11 (0.00037 vs 1.8e-08) | 0.00015 vs 0.0005 (0.00015 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 30 | 0.00023 vs 0.00091 (0.085 vs 0.044) | 5.8e-05 vs 0.00047 (0.062 vs 0.018) | 1.6e-05 vs 0.00027 (0.12 vs 0.057) | 1.1e-05 vs 2.7e-05 (0.005 vs 0.00034) | 6.5e-09 vs 6.4e-07 (6.5e-09 vs 6.4e-07) | 3.8e-07 vs 4.7e-11 (0.0004 vs 1.8e-08) | 6.5e-05 vs 0.0005 (6.5e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 40 | 0.00024 vs 0.00091 (0.12 vs 0.044) | 5.7e-05 vs 0.00047 (0.085 vs 0.018) | 1.5e-05 vs 0.00027 (0.15 vs 0.057) | 1.1e-05 vs 2.7e-05 (0.0073 vs 0.00034) | 6.5e-09 vs 6.4e-07 (6.5e-09 vs 6.4e-07) | 3.8e-07 vs 4.7e-11 (0.00059 vs 1.8e-08) | 6.4e-05 vs 0.0005 (6.4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 10 | 0.00043 vs 0.00091 (0.021 vs 0.044) | 0.00017 vs 0.00047 (0.014 vs 0.018) | 9.5e-05 vs 0.00027 (0.041 vs 0.057) | 6.1e-05 vs 2.7e-05 (0.0021 vs 0.00034) | 2.7e-07 vs 6.4e-07 (2.7e-07 vs 6.4e-07) | 4.6e-06 vs 4.7e-11 (0.00023 vs 1.8e-08) | 0.00016 vs 0.0005 (0.00016 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 20 | 0.00016 vs 0.00091 (0.043 vs 0.044) | 4.5e-05 vs 0.00047 (0.032 vs 0.018) | 1.4e-05 vs 0.00027 (0.076 vs 0.057) | 1e-05 vs 2.7e-05 (0.0023 vs 0.00034) | 6.5e-09 vs 6.4e-07 (6.5e-09 vs 6.4e-07) | 3.7e-07 vs 4.7e-11 (0.00018 vs 1.8e-08) | 4.7e-05 vs 0.0005 (4.7e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 30 | 0.0002 vs 0.00091 (0.078 vs 0.044) | 5.1e-05 vs 0.00047 (0.058 vs 0.018) | 1.5e-05 vs 0.00027 (0.11 vs 0.057) | 1e-05 vs 2.7e-05 (0.0042 vs 0.00034) | 6.5e-09 vs 6.4e-07 (6.5e-09 vs 6.4e-07) | 3.7e-07 vs 4.7e-11 (0.00032 vs 1.8e-08) | 5.5e-05 vs 0.0005 (5.5e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 40 | 0.00017 vs 0.00091 (0.1 vs 0.044) | 4.4e-05 vs 0.00047 (0.075 vs 0.018) | 1.3e-05 vs 0.00027 (0.14 vs 0.057) | 9.6e-06 vs 2.7e-05 (0.0055 vs 0.00034) | 6.5e-09 vs 6.4e-07 (6.5e-09 vs 6.4e-07) | 3.6e-07 vs 4.7e-11 (0.00042 vs 1.8e-08) | 4.8e-05 vs 0.0005 (4.8e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 20 | 0.00011 vs 0.00091 (0.038 vs 0.044) | 3.3e-05 vs 0.00047 (0.028 vs 0.018) | 1.1e-05 vs 0.00027 (0.07 vs 0.057) | 7.9e-06 vs 2.7e-05 (0.0018 vs 0.00034) | 6.3e-09 vs 6.4e-07 (6.3e-09 vs 6.4e-07) | 3.2e-07 vs 4.7e-11 (0.00014 vs 1.8e-08) | 3.4e-05 vs 0.0005 (3.4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 30 | 8.3e-05 vs 0.00091 (0.069 vs 0.044) | 2e-05 vs 0.00047 (0.051 vs 0.018) | 5.1e-06 vs 0.00027 (0.1 vs 0.057) | 3.3e-06 vs 2.7e-05 (0.003 vs 0.00034) | 1.2e-09 vs 6.4e-07 (1.2e-09 vs 6.4e-07) | 8.6e-08 vs 4.7e-11 (0.00021 vs 1.8e-08) | 2e-05 vs 0.0005 (2e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 40 | 7.8e-05 vs 0.00091 (0.089 vs 0.044) | 1.9e-05 vs 0.00047 (0.066 vs 0.018) | 5e-06 vs 0.00027 (0.12 vs 0.057) | 3.2e-06 vs 2.7e-05 (0.0038 vs 0.00034) | 1.2e-09 vs 6.4e-07 (1.2e-09 vs 6.4e-07) | 8.5e-08 vs 4.7e-11 (0.00026 vs 1.8e-08) | 1.9e-05 vs 0.0005 (1.9e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.0001, cap 20 | 8e-06 vs 0.00091 (0.013 vs 0.044) | 1.9e-06 vs 0.00047 (0.01 vs 0.018) | 4.2e-07 vs 0.00027 (0.04 vs 0.057) | 2.8e-07 vs 2.7e-05 (0.00036 vs 0.00034) | 2.6e-11 vs 6.4e-07 (2.6e-11 vs 6.4e-07) | 5e-09 vs 4.7e-11 (2e-05 vs 1.8e-08) | 1.9e-06 vs 0.0005 (1.9e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.0001, cap 30 | 5.4e-06 vs 0.00091 (0.028 vs 0.044) | 9.8e-07 vs 0.00047 (0.023 vs 0.018) | 1.6e-07 vs 0.00027 (0.06 vs 0.057) | 1.3e-07 vs 2.7e-05 (0.00064 vs 0.00034) | 3.6e-12 vs 6.4e-07 (3.6e-12 vs 6.4e-07) | 1.6e-09 vs 4.7e-11 (3.5e-05 vs 1.8e-08) | 1.2e-06 vs 0.0005 (1.2e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.0001, cap 40 | 3.3e-06 vs 0.00091 (0.05 vs 0.044) | 5e-07 vs 0.00047 (0.039 vs 0.018) | 6.2e-08 vs 0.00027 (0.081 vs 0.057) | 4.6e-08 vs 2.7e-05 (0.0011 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | 4e-10 vs 4.7e-11 (5.6e-05 vs 1.8e-08) | 6e-07 vs 0.0005 (6e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 10 | 0.011 vs 0.00091 (0.089 vs 0.044) | 0.0056 vs 0.00047 (0.06 vs 0.018) | 0.0068 vs 0.00027 (0.1 vs 0.057) | 0.0024 vs 2.7e-05 (0.015 vs 0.00034) | 0.00032 vs 6.4e-07 (0.00032 vs 6.4e-07) | 0.00024 vs 4.7e-11 (0.0017 vs 1.8e-08) | 0.0047 vs 0.0005 (0.0047 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 20 | 0.0078 vs 0.00091 (0.13 vs 0.044) | 0.0028 vs 0.00047 (0.09 vs 0.018) | 0.0032 vs 0.00027 (0.14 vs 0.057) | 0.00097 vs 2.7e-05 (0.015 vs 0.00034) | 5e-05 vs 6.4e-07 (5e-05 vs 6.4e-07) | 5.4e-05 vs 4.7e-11 (0.0011 vs 1.8e-08) | 0.0028 vs 0.0005 (0.0028 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 30 | 0.0063 vs 0.00091 (0.15 vs 0.044) | 0.0023 vs 0.00047 (0.1 vs 0.018) | 0.0027 vs 0.00027 (0.16 vs 0.057) | 0.00077 vs 2.7e-05 (0.015 vs 0.00034) | 4.7e-05 vs 6.4e-07 (4.7e-05 vs 6.4e-07) | 4.6e-05 vs 4.7e-11 (0.00096 vs 1.8e-08) | 0.0022 vs 0.0005 (0.0022 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 40 | 0.0042 vs 0.00091 (0.18 vs 0.044) | 0.0011 vs 0.00047 (0.11 vs 0.018) | 0.0011 vs 0.00027 (0.18 vs 0.057) | 0.00033 vs 2.7e-05 (0.016 vs 0.00034) | 6.7e-06 vs 6.4e-07 (6.7e-06 vs 6.4e-07) | 1.2e-05 vs 4.7e-11 (0.00083 vs 1.8e-08) | 0.0013 vs 0.0005 (0.0013 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 10 | 0.004 vs 0.00091 (0.044 vs 0.044) | 0.0019 vs 0.00047 (0.027 vs 0.018) | 0.0023 vs 0.00027 (0.061 vs 0.057) | 0.00064 vs 2.7e-05 (0.0059 vs 0.00034) | 4.6e-05 vs 6.4e-07 (4.6e-05 vs 6.4e-07) | 4.4e-05 vs 4.7e-11 (0.00049 vs 1.8e-08) | 0.0014 vs 0.0005 (0.0014 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 20 | 0.0023 vs 0.00091 (0.089 vs 0.044) | 0.00069 vs 0.00047 (0.059 vs 0.018) | 0.00071 vs 0.00027 (0.11 vs 0.057) | 0.00023 vs 2.7e-05 (0.0069 vs 0.00034) | 6.1e-06 vs 6.4e-07 (6.1e-06 vs 6.4e-07) | 9.7e-06 vs 4.7e-11 (0.00039 vs 1.8e-08) | 0.00078 vs 0.0005 (0.00078 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 30 | 0.0015 vs 0.00091 (0.13 vs 0.044) | 0.00034 vs 0.00047 (0.083 vs 0.018) | 0.00033 vs 0.00027 (0.14 vs 0.057) | 9.1e-05 vs 2.7e-05 (0.0082 vs 0.00034) | 9.5e-07 vs 6.4e-07 (9.5e-07 vs 6.4e-07) | 2.3e-06 vs 4.7e-11 (0.00033 vs 1.8e-08) | 0.00044 vs 0.0005 (0.00044 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 40 | 0.0012 vs 0.00091 (0.14 vs 0.044) | 0.00027 vs 0.00047 (0.093 vs 0.018) | 0.00027 vs 0.00027 (0.15 vs 0.057) | 7e-05 vs 2.7e-05 (0.009 vs 0.00034) | 8.7e-07 vs 6.4e-07 (8.7e-07 vs 6.4e-07) | 1.9e-06 vs 4.7e-11 (0.00033 vs 1.8e-08) | 0.00033 vs 0.0005 (0.00033 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 10 | 0.0014 vs 0.00091 (0.031 vs 0.044) | 0.00053 vs 0.00047 (0.019 vs 0.018) | 0.00058 vs 0.00027 (0.045 vs 0.057) | 0.00019 vs 2.7e-05 (0.0031 vs 0.00034) | 6e-06 vs 6.4e-07 (6e-06 vs 6.4e-07) | 9.2e-06 vs 4.7e-11 (0.00021 vs 1.8e-08) | 0.00052 vs 0.0005 (0.00052 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 20 | 0.00095 vs 0.00091 (0.071 vs 0.044) | 0.00026 vs 0.00047 (0.047 vs 0.018) | 0.00026 vs 0.00027 (0.09 vs 0.057) | 6.7e-05 vs 2.7e-05 (0.004 vs 0.00034) | 8.7e-07 vs 6.4e-07 (8.7e-07 vs 6.4e-07) | 1.9e-06 vs 4.7e-11 (0.00017 vs 1.8e-08) | 0.00028 vs 0.0005 (0.00028 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 30 | 0.00059 vs 0.00091 (0.1 vs 0.044) | 0.00011 vs 0.00047 (0.067 vs 0.018) | 0.0001 vs 0.00027 (0.11 vs 0.057) | 2.7e-05 vs 2.7e-05 (0.0049 vs 0.00034) | 1.3e-07 vs 6.4e-07 (1.3e-07 vs 6.4e-07) | 4.7e-07 vs 4.7e-11 (0.00017 vs 1.8e-08) | 0.00016 vs 0.0005 (0.00016 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 40 | 0.00045 vs 0.00091 (0.12 vs 0.044) | 8.2e-05 vs 0.00047 (0.082 vs 0.018) | 7.2e-05 vs 0.00027 (0.13 vs 0.057) | 2.1e-05 vs 2.7e-05 (0.0059 vs 0.00034) | 1.1e-07 vs 6.4e-07 (1.1e-07 vs 6.4e-07) | 3.9e-07 vs 4.7e-11 (0.00018 vs 1.8e-08) | 0.00012 vs 0.0005 (0.00012 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 10 | 0.00061 vs 0.00091 (0.023 vs 0.044) | 0.0002 vs 0.00047 (0.014 vs 0.018) | 0.00021 vs 0.00027 (0.039 vs 0.057) | 5.5e-05 vs 2.7e-05 (0.0016 vs 0.00034) | 8.6e-07 vs 6.4e-07 (8.6e-07 vs 6.4e-07) | 1.7e-06 vs 4.7e-11 (8.3e-05 vs 1.8e-08) | 0.00019 vs 0.0005 (0.00019 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 20 | 0.00036 vs 0.00091 (0.049 vs 0.044) | 7.6e-05 vs 0.00047 (0.033 vs 0.018) | 6.9e-05 vs 0.00027 (0.071 vs 0.057) | 2e-05 vs 2.7e-05 (0.0022 vs 0.00034) | 1.1e-07 vs 6.4e-07 (1.1e-07 vs 6.4e-07) | 3.9e-07 vs 4.7e-11 (8.1e-05 vs 1.8e-08) | 0.0001 vs 0.0005 (0.0001 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 30 | 0.0002 vs 0.00091 (0.086 vs 0.044) | 3.1e-05 vs 0.00047 (0.058 vs 0.018) | 2.7e-05 vs 0.00027 (0.1 vs 0.057) | 6.3e-06 vs 2.7e-05 (0.0031 vs 0.00034) | 1.6e-08 vs 6.4e-07 (1.6e-08 vs 6.4e-07) | 7.5e-08 vs 4.7e-11 (8.3e-05 vs 1.8e-08) | 4.8e-05 vs 0.0005 (4.8e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 40 | 0.00018 vs 0.00091 (0.11 vs 0.044) | 3e-05 vs 0.00047 (0.07 vs 0.018) | 2.6e-05 vs 0.00027 (0.12 vs 0.057) | 6.1e-06 vs 2.7e-05 (0.0038 vs 0.00034) | 1.6e-08 vs 6.4e-07 (1.6e-08 vs 6.4e-07) | 7.5e-08 vs 4.7e-11 (9.5e-05 vs 1.8e-08) | 4.4e-05 vs 0.0005 (4.4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 10 | 0.00021 vs 0.00091 (0.017 vs 0.044) | 5.6e-05 vs 0.00047 (0.011 vs 0.018) | 5.4e-05 vs 0.00027 (0.03 vs 0.057) | 1.6e-05 vs 2.7e-05 (0.00093 vs 0.00034) | 1.1e-07 vs 6.4e-07 (1.1e-07 vs 6.4e-07) | 3.6e-07 vs 4.7e-11 (4e-05 vs 1.8e-08) | 6.8e-05 vs 0.0005 (6.8e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 20 | 0.0002 vs 0.00091 (0.043 vs 0.044) | 3.7e-05 vs 0.00047 (0.029 vs 0.018) | 3.2e-05 vs 0.00027 (0.064 vs 0.057) | 8e-06 vs 2.7e-05 (0.0016 vs 0.00034) | 1.8e-08 vs 6.4e-07 (1.8e-08 vs 6.4e-07) | 9.4e-08 vs 4.7e-11 (5.2e-05 vs 1.8e-08) | 5.4e-05 vs 0.0005 (5.4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 30 | 8e-05 vs 0.00091 (0.068 vs 0.044) | 9.7e-06 vs 0.00047 (0.047 vs 0.018) | 7.3e-06 vs 0.00027 (0.086 vs 0.057) | 1.9e-06 vs 2.7e-05 (0.002 vs 0.00034) | 2.1e-09 vs 6.4e-07 (2.1e-09 vs 6.4e-07) | 1.6e-08 vs 4.7e-11 (4.6e-05 vs 1.8e-08) | 1.8e-05 vs 0.0005 (1.8e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 40 | 7.8e-05 vs 0.00091 (0.096 vs 0.044) | 9.5e-06 vs 0.00047 (0.065 vs 0.018) | 7.2e-06 vs 0.00027 (0.11 vs 0.057) | 1.9e-06 vs 2.7e-05 (0.0028 vs 0.00034) | 2.1e-09 vs 6.4e-07 (2.1e-09 vs 6.4e-07) | 1.6e-08 vs 4.7e-11 (6.4e-05 vs 1.8e-08) | 1.8e-05 vs 0.0005 (1.8e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 10 | 0.00021 vs 0.00091 (0.017 vs 0.044) | 5.6e-05 vs 0.00047 (0.011 vs 0.018) | 5.4e-05 vs 0.00027 (0.03 vs 0.057) | 1.6e-05 vs 2.7e-05 (0.00093 vs 0.00034) | 1.1e-07 vs 6.4e-07 (1.1e-07 vs 6.4e-07) | 3.6e-07 vs 4.7e-11 (4e-05 vs 1.8e-08) | 6.8e-05 vs 0.0005 (6.8e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 20 | 6e-05 vs 0.00091 (0.034 vs 0.044) | 8.7e-06 vs 0.00047 (0.024 vs 0.018) | 6.8e-06 vs 0.00027 (0.057 vs 0.057) | 1.8e-06 vs 2.7e-05 (0.00092 vs 0.00034) | 2.1e-09 vs 6.4e-07 (2.1e-09 vs 6.4e-07) | 1.6e-08 vs 4.7e-11 (2.3e-05 vs 1.8e-08) | 1.5e-05 vs 0.0005 (1.5e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 30 | 6.9e-05 vs 0.00091 (0.063 vs 0.044) | 9.1e-06 vs 0.00047 (0.043 vs 0.018) | 7e-06 vs 0.00027 (0.082 vs 0.057) | 1.8e-06 vs 2.7e-05 (0.0016 vs 0.00034) | 2.1e-09 vs 6.4e-07 (2.1e-09 vs 6.4e-07) | 1.6e-08 vs 4.7e-11 (3.8e-05 vs 1.8e-08) | 1.6e-05 vs 0.0005 (1.6e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 40 | 6e-05 vs 0.00091 (0.083 vs 0.044) | 8.2e-06 vs 0.00047 (0.056 vs 0.018) | 6.4e-06 vs 0.00027 (0.097 vs 0.057) | 1.7e-06 vs 2.7e-05 (0.0021 vs 0.00034) | 2.1e-09 vs 6.4e-07 (2.1e-09 vs 6.4e-07) | 1.6e-08 vs 4.7e-11 (4.5e-05 vs 1.8e-08) | 1.4e-05 vs 0.0005 (1.4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 20 | 4.4e-05 vs 0.00091 (0.03 vs 0.044) | 6.9e-06 vs 0.00047 (0.021 vs 0.018) | 5.6e-06 vs 0.00027 (0.052 vs 0.057) | 1.5e-06 vs 2.7e-05 (0.00071 vs 0.00034) | 2.1e-09 vs 6.4e-07 (2.1e-09 vs 6.4e-07) | 1.5e-08 vs 4.7e-11 (1.7e-05 vs 1.8e-08) | 1.1e-05 vs 0.0005 (1.1e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 30 | 2.7e-05 vs 0.00091 (0.055 vs 0.044) | 3.2e-06 vs 0.00047 (0.039 vs 0.018) | 2.4e-06 vs 0.00027 (0.074 vs 0.057) | 5.1e-07 vs 2.7e-05 (0.0011 vs 0.00034) | 3e-10 vs 6.4e-07 (3e-10 vs 6.4e-07) | 2.9e-09 vs 4.7e-11 (2.2e-05 vs 1.8e-08) | 5.5e-06 vs 0.0005 (5.5e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 40 | 2.5e-05 vs 0.00091 (0.072 vs 0.044) | 3.1e-06 vs 0.00047 (0.05 vs 0.018) | 2.4e-06 vs 0.00027 (0.087 vs 0.057) | 5e-07 vs 2.7e-05 (0.0014 vs 0.00034) | 3e-10 vs 6.4e-07 (3e-10 vs 6.4e-07) | 2.9e-09 vs 4.7e-11 (2.6e-05 vs 1.8e-08) | 5.2e-06 vs 0.0005 (5.2e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.0001, cap 20 | 2.6e-06 vs 0.00091 (0.01 vs 0.044) | 2.6e-07 vs 0.00047 (0.0079 vs 0.018) | 1.8e-07 vs 0.00027 (0.029 vs 0.057) | 3.6e-08 vs 2.7e-05 (0.00012 vs 0.00034) | 5.6e-12 vs 6.4e-07 (5.6e-12 vs 6.4e-07) | 1.1e-10 vs 4.7e-11 (2e-06 vs 1.8e-08) | 4.9e-07 vs 0.0005 (4.9e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.0001, cap 30 | 1.5e-06 vs 0.00091 (0.022 vs 0.044) | 9.9e-08 vs 0.00047 (0.017 vs 0.018) | 5.9e-08 vs 0.00027 (0.046 vs 0.057) | 1.3e-08 vs 2.7e-05 (0.00021 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | 2.5e-11 vs 4.7e-11 (3.1e-06 vs 1.8e-08) | 2.6e-07 vs 0.0005 (2.6e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.0001, cap 40 | 7.6e-07 vs 0.00091 (0.039 vs 0.044) | 3.9e-08 vs 0.00047 (0.029 vs 0.018) | 2.3e-08 vs 0.00027 (0.06 vs 0.057) | 4e-09 vs 2.7e-05 (0.00033 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | 4.7e-12 vs 4.7e-11 (4.5e-06 vs 1.8e-08) | 1.1e-07 vs 0.0005 (1.1e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 10 | 0.0068 vs 0.00091 (0.074 vs 0.044) | 0.005 vs 0.00047 (0.045 vs 0.018) | 0.0036 vs 0.00027 (0.09 vs 0.057) | 0.0011 vs 2.7e-05 (0.0093 vs 0.00034) | 0.00017 vs 6.4e-07 (0.00017 vs 6.4e-07) | 4.5e-05 vs 4.7e-11 (0.00044 vs 1.8e-08) | 0.0034 vs 0.0005 (0.0034 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 20 | 0.0042 vs 0.00091 (0.11 vs 0.044) | 0.0025 vs 0.00047 (0.066 vs 0.018) | 0.0012 vs 0.00027 (0.12 vs 0.057) | 0.00042 vs 2.7e-05 (0.0089 vs 0.00034) | 1.9e-05 vs 6.4e-07 (1.9e-05 vs 6.4e-07) | 6.4e-06 vs 4.7e-11 (0.00021 vs 1.8e-08) | 0.0018 vs 0.0005 (0.0018 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 30 | 0.0033 vs 0.00091 (0.13 vs 0.044) | 0.002 vs 0.00047 (0.073 vs 0.018) | 0.001 vs 0.00027 (0.13 vs 0.057) | 0.00033 vs 2.7e-05 (0.0085 vs 0.00034) | 1.8e-05 vs 6.4e-07 (1.8e-05 vs 6.4e-07) | 5.8e-06 vs 4.7e-11 (0.00017 vs 1.8e-08) | 0.0014 vs 0.0005 (0.0014 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 40 | 0.0019 vs 0.00091 (0.15 vs 0.044) | 0.00092 vs 0.00047 (0.083 vs 0.018) | 0.00031 vs 0.00027 (0.15 vs 0.057) | 0.00012 vs 2.7e-05 (0.0088 vs 0.00034) | 2.5e-06 vs 6.4e-07 (2.5e-06 vs 6.4e-07) | 1e-06 vs 4.7e-11 (0.00012 vs 1.8e-08) | 0.00077 vs 0.0005 (0.00077 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 10 | 0.0024 vs 0.00091 (0.036 vs 0.044) | 0.0016 vs 0.00047 (0.02 vs 0.018) | 0.00097 vs 0.00027 (0.054 vs 0.057) | 0.00028 vs 2.7e-05 (0.0034 vs 0.00034) | 1.8e-05 vs 6.4e-07 (1.8e-05 vs 6.4e-07) | 5.7e-06 vs 4.7e-11 (0.00011 vs 1.8e-08) | 0.00098 vs 0.0005 (0.00098 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 20 | 0.0011 vs 0.00091 (0.073 vs 0.044) | 0.0006 vs 0.00047 (0.042 vs 0.018) | 0.00023 vs 0.00027 (0.089 vs 0.057) | 8.5e-05 vs 2.7e-05 (0.0038 vs 0.00034) | 2.3e-06 vs 6.4e-07 (2.3e-06 vs 6.4e-07) | 9.1e-07 vs 4.7e-11 (6.3e-05 vs 1.8e-08) | 0.00048 vs 0.0005 (0.00048 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 30 | 0.00063 vs 0.00091 (0.1 vs 0.044) | 0.00029 vs 0.00047 (0.057 vs 0.018) | 8.1e-05 vs 0.00027 (0.11 vs 0.057) | 3.3e-05 vs 2.7e-05 (0.0042 vs 0.00034) | 2.7e-07 vs 6.4e-07 (2.7e-07 vs 6.4e-07) | 1.3e-07 vs 4.7e-11 (4.2e-05 vs 1.8e-08) | 0.00024 vs 0.0005 (0.00024 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 40 | 0.0005 vs 0.00091 (0.12 vs 0.044) | 0.00023 vs 0.00047 (0.064 vs 0.018) | 6.8e-05 vs 0.00027 (0.12 vs 0.057) | 2.5e-05 vs 2.7e-05 (0.0045 vs 0.00034) | 2.5e-07 vs 6.4e-07 (2.5e-07 vs 6.4e-07) | 1.2e-07 vs 4.7e-11 (3.7e-05 vs 1.8e-08) | 0.00018 vs 0.0005 (0.00018 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 10 | 0.00076 vs 0.00091 (0.025 vs 0.044) | 0.00047 vs 0.00047 (0.014 vs 0.018) | 0.00021 vs 0.00027 (0.039 vs 0.057) | 7.1e-05 vs 2.7e-05 (0.0017 vs 0.00034) | 2.3e-06 vs 6.4e-07 (2.3e-06 vs 6.4e-07) | 8.9e-07 vs 4.7e-11 (4.1e-05 vs 1.8e-08) | 0.00034 vs 0.0005 (0.00034 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 20 | 0.00044 vs 0.00091 (0.057 vs 0.044) | 0.00022 vs 0.00047 (0.033 vs 0.018) | 6.7e-05 vs 0.00027 (0.076 vs 0.057) | 2.5e-05 vs 2.7e-05 (0.0021 vs 0.00034) | 2.5e-07 vs 6.4e-07 (2.5e-07 vs 6.4e-07) | 1.2e-07 vs 4.7e-11 (2.4e-05 vs 1.8e-08) | 0.00016 vs 0.0005 (0.00016 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 30 | 0.00023 vs 0.00091 (0.082 vs 0.044) | 9.4e-05 vs 0.00047 (0.046 vs 0.018) | 2e-05 vs 0.00027 (0.095 vs 0.057) | 8.9e-06 vs 2.7e-05 (0.0024 vs 0.00034) | 3.5e-08 vs 6.4e-07 (3.5e-08 vs 6.4e-07) | 2e-08 vs 4.7e-11 (1.9e-05 vs 1.8e-08) | 8.4e-05 vs 0.0005 (8.4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 40 | 0.00017 vs 0.00091 (0.1 vs 0.044) | 6.9e-05 vs 0.00047 (0.055 vs 0.018) | 1.5e-05 vs 0.00027 (0.11 vs 0.057) | 6.5e-06 vs 2.7e-05 (0.0028 vs 0.00034) | 3.3e-08 vs 6.4e-07 (3.3e-08 vs 6.4e-07) | 1.8e-08 vs 4.7e-11 (1.8e-05 vs 1.8e-08) | 6.4e-05 vs 0.0005 (6.4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 10 | 0.00031 vs 0.00091 (0.019 vs 0.044) | 0.00017 vs 0.00047 (0.0098 vs 0.018) | 6.1e-05 vs 0.00027 (0.035 vs 0.057) | 2.1e-05 vs 2.7e-05 (0.00087 vs 0.00034) | 2.5e-07 vs 6.4e-07 (2.5e-07 vs 6.4e-07) | 1.1e-07 vs 4.7e-11 (1.4e-05 vs 1.8e-08) | 0.00011 vs 0.0005 (0.00011 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 20 | 0.00015 vs 0.00091 (0.039 vs 0.044) | 6.4e-05 vs 0.00047 (0.023 vs 0.018) | 1.5e-05 vs 0.00027 (0.062 vs 0.057) | 6.4e-06 vs 2.7e-05 (0.0011 vs 0.00034) | 3.3e-08 vs 6.4e-07 (3.3e-08 vs 6.4e-07) | 1.8e-08 vs 4.7e-11 (1e-05 vs 1.8e-08) | 5.7e-05 vs 0.0005 (5.7e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 30 | 7.1e-05 vs 0.00091 (0.069 vs 0.044) | 2.6e-05 vs 0.00047 (0.039 vs 0.018) | 4.4e-06 vs 0.00027 (0.084 vs 0.057) | 1.9e-06 vs 2.7e-05 (0.0015 vs 0.00034) | 3.5e-09 vs 6.4e-07 (3.5e-09 vs 6.4e-07) | 2.3e-09 vs 4.7e-11 (7.9e-06 vs 1.8e-08) | 2.3e-05 vs 0.0005 (2.3e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 40 | 6.6e-05 vs 0.00091 (0.084 vs 0.044) | 2.4e-05 vs 0.00047 (0.046 vs 0.018) | 4.3e-06 vs 0.00027 (0.096 vs 0.057) | 1.9e-06 vs 2.7e-05 (0.0017 vs 0.00034) | 3.5e-09 vs 6.4e-07 (3.5e-09 vs 6.4e-07) | 2.3e-09 vs 4.7e-11 (8.5e-06 vs 1.8e-08) | 2.1e-05 vs 0.0005 (2.1e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 10 | 9.8e-05 vs 0.00091 (0.014 vs 0.044) | 4.8e-05 vs 0.00047 (0.0073 vs 0.018) | 1.3e-05 vs 0.00027 (0.027 vs 0.057) | 5.2e-06 vs 2.7e-05 (0.00048 vs 0.00034) | 3.2e-08 vs 6.4e-07 (3.2e-08 vs 6.4e-07) | 1.8e-08 vs 4.7e-11 (5.9e-06 vs 1.8e-08) | 4e-05 vs 0.0005 (4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 20 | 7.7e-05 vs 0.00091 (0.034 vs 0.044) | 3e-05 vs 0.00047 (0.02 vs 0.018) | 5.3e-06 vs 0.00027 (0.056 vs 0.057) | 2.5e-06 vs 2.7e-05 (0.0008 vs 0.00034) | 3.9e-09 vs 6.4e-07 (3.9e-09 vs 6.4e-07) | 2.7e-09 vs 4.7e-11 (5.9e-06 vs 1.8e-08) | 2.7e-05 vs 0.0005 (2.7e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 30 | 2.5e-05 vs 0.00091 (0.054 vs 0.044) | 7.9e-06 vs 0.00047 (0.032 vs 0.018) | 9.9e-07 vs 0.00027 (0.073 vs 0.057) | 5.1e-07 vs 2.7e-05 (0.00089 vs 0.00034) | 4.6e-10 vs 6.4e-07 (4.6e-10 vs 6.4e-07) | 3.7e-10 vs 4.7e-11 (4.1e-06 vs 1.8e-08) | 8.4e-06 vs 0.0005 (8.4e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 40 | 2.5e-05 vs 0.00091 (0.077 vs 0.044) | 7.7e-06 vs 0.00047 (0.043 vs 0.018) | 9.9e-07 vs 0.00027 (0.09 vs 0.057) | 5e-07 vs 2.7e-05 (0.0013 vs 0.00034) | 4.6e-10 vs 6.4e-07 (4.6e-10 vs 6.4e-07) | 3.7e-10 vs 4.7e-11 (5.2e-06 vs 1.8e-08) | 8.2e-06 vs 0.0005 (8.2e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 10 | 9.8e-05 vs 0.00091 (0.014 vs 0.044) | 4.8e-05 vs 0.00047 (0.0073 vs 0.018) | 1.3e-05 vs 0.00027 (0.027 vs 0.057) | 5.2e-06 vs 2.7e-05 (0.00048 vs 0.00034) | 3.2e-08 vs 6.4e-07 (3.2e-08 vs 6.4e-07) | 1.8e-08 vs 4.7e-11 (5.9e-06 vs 1.8e-08) | 4e-05 vs 0.0005 (4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 20 | 2.1e-05 vs 0.00091 (0.027 vs 0.044) | 7.1e-06 vs 0.00047 (0.016 vs 0.018) | 9.7e-07 vs 0.00027 (0.051 vs 0.057) | 4.8e-07 vs 2.7e-05 (0.00043 vs 0.00034) | 4.6e-10 vs 6.4e-07 (4.6e-10 vs 6.4e-07) | 3.7e-10 vs 4.7e-11 (2.3e-06 vs 1.8e-08) | 7.2e-06 vs 0.0005 (7.2e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 30 | 2.3e-05 vs 0.00091 (0.05 vs 0.044) | 7.4e-06 vs 0.00047 (0.029 vs 0.018) | 9.8e-07 vs 0.00027 (0.07 vs 0.057) | 4.9e-07 vs 2.7e-05 (0.00074 vs 0.00034) | 4.6e-10 vs 6.4e-07 (4.6e-10 vs 6.4e-07) | 3.7e-10 vs 4.7e-11 (3.3e-06 vs 1.8e-08) | 7.6e-06 vs 0.0005 (7.6e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 40 | 2e-05 vs 0.00091 (0.066 vs 0.044) | 6.7e-06 vs 0.00047 (0.038 vs 0.018) | 9.4e-07 vs 0.00027 (0.081 vs 0.057) | 4.6e-07 vs 2.7e-05 (0.00092 vs 0.00034) | 4.6e-10 vs 6.4e-07 (4.6e-10 vs 6.4e-07) | 3.6e-10 vs 4.7e-11 (3.7e-06 vs 1.8e-08) | 6.9e-06 vs 0.0005 (6.9e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 20 | 1.6e-05 vs 0.00091 (0.023 vs 0.044) | 5.7e-06 vs 0.00047 (0.014 vs 0.018) | 8.7e-07 vs 0.00027 (0.047 vs 0.057) | 4.1e-07 vs 2.7e-05 (0.00033 vs 0.00034) | 4.5e-10 vs 6.4e-07 (4.5e-10 vs 6.4e-07) | 3.6e-10 vs 4.7e-11 (1.7e-06 vs 1.8e-08) | 5.5e-06 vs 0.0005 (5.5e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 30 | 8.3e-06 vs 0.00091 (0.043 vs 0.044) | 2.5e-06 vs 0.00047 (0.026 vs 0.018) | 2.7e-07 vs 0.00027 (0.064 vs 0.057) | 1.4e-07 vs 2.7e-05 (0.00048 vs 0.00034) | 4.9e-11 vs 6.4e-07 (4.9e-11 vs 6.4e-07) | 4.7e-11 vs 4.7e-11 (1.7e-06 vs 1.8e-08) | 2.4e-06 vs 0.0005 (2.4e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 40 | 7.9e-06 vs 0.00091 (0.056 vs 0.044) | 2.4e-06 vs 0.00047 (0.033 vs 0.018) | 2.7e-07 vs 0.00027 (0.074 vs 0.057) | 1.4e-07 vs 2.7e-05 (0.00059 vs 0.00034) | 4.9e-11 vs 6.4e-07 (4.9e-11 vs 6.4e-07) | 4.7e-11 vs 4.7e-11 (1.9e-06 vs 1.8e-08) | 2.3e-06 vs 0.0005 (2.3e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.0001, cap 20 | 7.5e-07 vs 0.00091 (0.0078 vs 0.044) | 2e-07 vs 0.00047 (0.0051 vs 0.018) | 1.5e-08 vs 0.00027 (0.027 vs 0.057) | 8.5e-09 vs 2.7e-05 (5.2e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.6e-07 vs 1.8e-08) | 2e-07 vs 0.0005 (2e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.0001, cap 30 | 3.5e-07 vs 0.00091 (0.017 vs 0.044) | 7.6e-08 vs 0.00047 (0.011 vs 0.018) | 3.9e-09 vs 0.00027 (0.043 vs 0.057) | 2.6e-09 vs 2.7e-05 (8.6e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (2e-07 vs 1.8e-08) | 9.9e-08 vs 0.0005 (9.9e-08 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.0001, cap 40 | 1.6e-07 vs 0.00091 (0.03 vs 0.044) | 3e-08 vs 0.00047 (0.02 vs 0.018) | 1.1e-09 vs 0.00027 (0.053 vs 0.057) | 7.7e-10 vs 2.7e-05 (0.00013 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (2.6e-07 vs 1.8e-08) | 3.7e-08 vs 0.0005 (3.7e-08 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 10 | 0.0041 vs 0.00091 (0.061 vs 0.044) | 0.0026 vs 0.00047 (0.036 vs 0.018) | 0.0024 vs 0.00027 (0.08 vs 0.057) | 0.00052 vs 2.7e-05 (0.0048 vs 0.00034) | 4.6e-05 vs 6.4e-07 (4.6e-05 vs 6.4e-07) | 8.1e-06 vs 4.7e-11 (9.8e-05 vs 1.8e-08) | 0.0018 vs 0.0005 (0.0018 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 20 | 0.0021 vs 0.00091 (0.092 vs 0.044) | 0.0009 vs 0.00047 (0.053 vs 0.018) | 0.00063 vs 0.00027 (0.11 vs 0.057) | 0.00018 vs 2.7e-05 (0.0041 vs 0.00034) | 5.1e-06 vs 6.4e-07 (5.1e-06 vs 6.4e-07) | 8.3e-07 vs 4.7e-11 (3.4e-05 vs 1.8e-08) | 0.00091 vs 0.0005 (0.00091 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 30 | 0.0017 vs 0.00091 (0.1 vs 0.044) | 0.00075 vs 0.00047 (0.06 vs 0.018) | 0.00055 vs 0.00027 (0.12 vs 0.057) | 0.00015 vs 2.7e-05 (0.0038 vs 0.00034) | 5e-06 vs 6.4e-07 (5e-06 vs 6.4e-07) | 7.9e-07 vs 4.7e-11 (2.8e-05 vs 1.8e-08) | 0.00069 vs 0.0005 (0.00069 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 40 | 0.00081 vs 0.00091 (0.12 vs 0.044) | 0.00026 vs 0.00047 (0.069 vs 0.018) | 0.00015 vs 0.00027 (0.13 vs 0.057) | 4.9e-05 vs 2.7e-05 (0.0037 vs 0.00034) | 4.6e-07 vs 6.4e-07 (4.6e-07 vs 6.4e-07) | 9.1e-08 vs 4.7e-11 (1.4e-05 vs 1.8e-08) | 0.00035 vs 0.0005 (0.00035 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 10 | 0.0013 vs 0.00091 (0.029 vs 0.044) | 0.00068 vs 0.00047 (0.016 vs 0.018) | 0.00052 vs 0.00027 (0.046 vs 0.057) | 0.00013 vs 2.7e-05 (0.0017 vs 0.00034) | 5e-06 vs 6.4e-07 (5e-06 vs 6.4e-07) | 7.8e-07 vs 4.7e-11 (2.1e-05 vs 1.8e-08) | 0.00052 vs 0.0005 (0.00052 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 20 | 0.00051 vs 0.00091 (0.059 vs 0.044) | 0.00019 vs 0.00047 (0.033 vs 0.018) | 0.00012 vs 0.00027 (0.079 vs 0.057) | 3.4e-05 vs 2.7e-05 (0.0016 vs 0.00034) | 4.3e-07 vs 6.4e-07 (4.3e-07 vs 6.4e-07) | 8.6e-08 vs 4.7e-11 (8.8e-06 vs 1.8e-08) | 0.00022 vs 0.0005 (0.00022 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 30 | 0.00026 vs 0.00091 (0.084 vs 0.044) | 6.9e-05 vs 0.00047 (0.046 vs 0.018) | 3.4e-05 vs 0.00027 (0.099 vs 0.057) | 1.2e-05 vs 2.7e-05 (0.0017 vs 0.00034) | 4.9e-08 vs 6.4e-07 (4.9e-08 vs 6.4e-07) | 8.9e-09 vs 4.7e-11 (4.4e-06 vs 1.8e-08) | 0.0001 vs 0.0005 (0.0001 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 40 | 0.0002 vs 0.00091 (0.096 vs 0.044) | 5.6e-05 vs 0.00047 (0.052 vs 0.018) | 2.8e-05 vs 0.00027 (0.11 vs 0.057) | 9.5e-06 vs 2.7e-05 (0.0018 vs 0.00034) | 4.6e-08 vs 6.4e-07 (4.6e-08 vs 6.4e-07) | 8.3e-09 vs 4.7e-11 (3.7e-06 vs 1.8e-08) | 7.8e-05 vs 0.0005 (7.8e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 10 | 0.00038 vs 0.00091 (0.02 vs 0.044) | 0.00017 vs 0.00047 (0.01 vs 0.018) | 0.00011 vs 0.00027 (0.033 vs 0.057) | 3e-05 vs 2.7e-05 (0.00079 vs 0.00034) | 4.3e-07 vs 6.4e-07 (4.3e-07 vs 6.4e-07) | 8.6e-08 vs 4.7e-11 (6.6e-06 vs 1.8e-08) | 0.00017 vs 0.0005 (0.00017 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 20 | 0.00019 vs 0.00091 (0.046 vs 0.044) | 5.5e-05 vs 0.00047 (0.025 vs 0.018) | 2.8e-05 vs 0.00027 (0.067 vs 0.057) | 9.3e-06 vs 2.7e-05 (0.00086 vs 0.00034) | 4.6e-08 vs 6.4e-07 (4.6e-08 vs 6.4e-07) | 8.3e-09 vs 4.7e-11 (2.8e-06 vs 1.8e-08) | 7.2e-05 vs 0.0005 (7.2e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 30 | 8.5e-05 vs 0.00091 (0.066 vs 0.044) | 1.9e-05 vs 0.00047 (0.036 vs 0.018) | 7.7e-06 vs 0.00027 (0.084 vs 0.057) | 3e-06 vs 2.7e-05 (0.00097 vs 0.00034) | 4.3e-09 vs 6.4e-07 (4.3e-09 vs 6.4e-07) | 9.8e-10 vs 4.7e-11 (1.7e-06 vs 1.8e-08) | 3.4e-05 vs 0.0005 (3.4e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 40 | 6.2e-05 vs 0.00091 (0.082 vs 0.044) | 1.5e-05 vs 0.00047 (0.044 vs 0.018) | 6.3e-06 vs 0.00027 (0.097 vs 0.057) | 2.2e-06 vs 2.7e-05 (0.0011 vs 0.00034) | 4e-09 vs 6.4e-07 (4e-09 vs 6.4e-07) | 9.2e-10 vs 4.7e-11 (1.5e-06 vs 1.8e-08) | 2.5e-05 vs 0.0005 (2.5e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 10 | 0.00014 vs 0.00091 (0.015 vs 0.044) | 4.8e-05 vs 0.00047 (0.0074 vs 0.018) | 2.6e-05 vs 0.00027 (0.029 vs 0.057) | 8.1e-06 vs 2.7e-05 (0.00038 vs 0.00034) | 4.6e-08 vs 6.4e-07 (4.6e-08 vs 6.4e-07) | 8.3e-09 vs 4.7e-11 (1.9e-06 vs 1.8e-08) | 5.3e-05 vs 0.0005 (5.3e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 20 | 5.7e-05 vs 0.00091 (0.031 vs 0.044) | 1.4e-05 vs 0.00047 (0.017 vs 0.018) | 6.2e-06 vs 0.00027 (0.053 vs 0.057) | 2.2e-06 vs 2.7e-05 (0.00045 vs 0.00034) | 4e-09 vs 6.4e-07 (4e-09 vs 6.4e-07) | 9.2e-10 vs 4.7e-11 (1.1e-06 vs 1.8e-08) | 2.3e-05 vs 0.0005 (2.3e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 30 | 2.3e-05 vs 0.00091 (0.055 vs 0.044) | 4.2e-06 vs 0.00047 (0.03 vs 0.018) | 1.4e-06 vs 0.00027 (0.075 vs 0.057) | 6.1e-07 vs 2.7e-05 (0.00056 vs 0.00034) | 4.3e-10 vs 6.4e-07 (4.3e-10 vs 6.4e-07) | 8.9e-11 vs 4.7e-11 (6.1e-07 vs 1.8e-08) | 8.7e-06 vs 0.0005 (8.7e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 40 | 2.2e-05 vs 0.00091 (0.068 vs 0.044) | 4.1e-06 vs 0.00047 (0.036 vs 0.018) | 1.4e-06 vs 0.00027 (0.086 vs 0.057) | 6e-07 vs 2.7e-05 (0.00067 vs 0.00034) | 4.3e-10 vs 6.4e-07 (4.3e-10 vs 6.4e-07) | 8.9e-11 vs 4.7e-11 (6.2e-07 vs 1.8e-08) | 8.2e-06 vs 0.0005 (8.2e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 10 | 4.1e-05 vs 0.00091 (0.011 vs 0.044) | 1.2e-05 vs 0.00047 (0.0053 vs 0.018) | 5.7e-06 vs 0.00027 (0.022 vs 0.057) | 1.9e-06 vs 2.7e-05 (0.0002 vs 0.00034) | 4e-09 vs 6.4e-07 (4e-09 vs 6.4e-07) | 9.1e-10 vs 4.7e-11 (6.9e-07 vs 1.8e-08) | 1.7e-05 vs 0.0005 (1.7e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 20 | 2.7e-05 vs 0.00091 (0.027 vs 0.044) | 5.2e-06 vs 0.00047 (0.014 vs 0.018) | 1.8e-06 vs 0.00027 (0.048 vs 0.057) | 7.8e-07 vs 2.7e-05 (0.00032 vs 0.00034) | 4.6e-10 vs 6.4e-07 (4.6e-10 vs 6.4e-07) | 9.6e-11 vs 4.7e-11 (5.4e-07 vs 1.8e-08) | 1.1e-05 vs 0.0005 (1.1e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 30 | 7.4e-06 vs 0.00091 (0.043 vs 0.044) | 1.1e-06 vs 0.00047 (0.023 vs 0.018) | 3.2e-07 vs 0.00027 (0.065 vs 0.057) | 1.4e-07 vs 2.7e-05 (0.00034 vs 0.00034) | 3.8e-11 vs 6.4e-07 (3.8e-11 vs 6.4e-07) | 9.7e-12 vs 4.7e-11 (2.9e-07 vs 1.8e-08) | 2.9e-06 vs 0.0005 (2.9e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 40 | 7.2e-06 vs 0.00091 (0.061 vs 0.044) | 1.1e-06 vs 0.00047 (0.033 vs 0.018) | 3.2e-07 vs 0.00027 (0.08 vs 0.057) | 1.4e-07 vs 2.7e-05 (0.00048 vs 0.00034) | 3.8e-11 vs 6.4e-07 (3.8e-11 vs 6.4e-07) | 9.7e-12 vs 4.7e-11 (3.3e-07 vs 1.8e-08) | 2.8e-06 vs 0.0005 (2.8e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 10 | 4.1e-05 vs 0.00091 (0.011 vs 0.044) | 1.2e-05 vs 0.00047 (0.0053 vs 0.018) | 5.7e-06 vs 0.00027 (0.022 vs 0.057) | 1.9e-06 vs 2.7e-05 (0.0002 vs 0.00034) | 4e-09 vs 6.4e-07 (4e-09 vs 6.4e-07) | 9.1e-10 vs 4.7e-11 (6.9e-07 vs 1.8e-08) | 1.7e-05 vs 0.0005 (1.7e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 20 | 6.5e-06 vs 0.00091 (0.021 vs 0.044) | 1.1e-06 vs 0.00047 (0.011 vs 0.018) | 3.2e-07 vs 0.00027 (0.043 vs 0.057) | 1.4e-07 vs 2.7e-05 (0.00016 vs 0.00034) | 3.8e-11 vs 6.4e-07 (3.8e-11 vs 6.4e-07) | 9.7e-12 vs 4.7e-11 (1.8e-07 vs 1.8e-08) | 2.6e-06 vs 0.0005 (2.6e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 30 | 6.9e-06 vs 0.00091 (0.039 vs 0.044) | 1.1e-06 vs 0.00047 (0.021 vs 0.018) | 3.2e-07 vs 0.00027 (0.062 vs 0.057) | 1.4e-07 vs 2.7e-05 (0.00028 vs 0.00034) | 3.8e-11 vs 6.4e-07 (3.8e-11 vs 6.4e-07) | 9.7e-12 vs 4.7e-11 (2.4e-07 vs 1.8e-08) | 2.7e-06 vs 0.0005 (2.7e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 40 | 6.2e-06 vs 0.00091 (0.052 vs 0.044) | 1e-06 vs 0.00047 (0.028 vs 0.018) | 3.1e-07 vs 0.00027 (0.073 vs 0.057) | 1.3e-07 vs 2.7e-05 (0.00035 vs 0.00034) | 3.8e-11 vs 6.4e-07 (3.8e-11 vs 6.4e-07) | 9.7e-12 vs 4.7e-11 (2.4e-07 vs 1.8e-08) | 2.4e-06 vs 0.0005 (2.4e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 20 | 5.2e-06 vs 0.00091 (0.018 vs 0.044) | 9.1e-07 vs 0.00047 (0.0097 vs 0.018) | 2.9e-07 vs 0.00027 (0.039 vs 0.057) | 1.2e-07 vs 2.7e-05 (0.00013 vs 0.00034) | 3.7e-11 vs 6.4e-07 (3.7e-11 vs 6.4e-07) | 9.6e-12 vs 4.7e-11 (1.4e-07 vs 1.8e-08) | 2e-06 vs 0.0005 (2e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 30 | 2.3e-06 vs 0.00091 (0.034 vs 0.044) | 2.9e-07 vs 0.00047 (0.018 vs 0.018) | 7.2e-08 vs 0.00027 (0.057 vs 0.057) | 3.7e-08 vs 2.7e-05 (0.00018 vs 0.00034) | 4e-12 vs 6.4e-07 (4e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1e-07 vs 1.8e-08) | 8.2e-07 vs 0.0005 (8.2e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 40 | 2.3e-06 vs 0.00091 (0.045 vs 0.044) | 2.9e-07 vs 0.00047 (0.024 vs 0.018) | 7.2e-08 vs 0.00027 (0.066 vs 0.057) | 3.7e-08 vs 2.7e-05 (0.00022 vs 0.00034) | 4e-12 vs 6.4e-07 (4e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.1e-07 vs 1.8e-08) | 7.9e-07 vs 0.0005 (7.9e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.0001, cap 20 | 1.9e-07 vs 0.00091 (0.0059 vs 0.044) | 1.8e-08 vs 0.00047 (0.0033 vs 0.018) | 3.3e-09 vs 0.00027 (0.021 vs 0.057) | 2e-09 vs 2.7e-05 (1.9e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (9.6e-09 vs 1.8e-08) | 6.4e-08 vs 0.0005 (6.4e-08 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.0001, cap 30 | 7.6e-08 vs 0.00091 (0.013 vs 0.044) | 5.4e-09 vs 0.00047 (0.0072 vs 0.018) | 8.1e-10 vs 0.00027 (0.034 vs 0.057) | 5.4e-10 vs 2.7e-05 (3.1e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1e-08 vs 1.8e-08) | 2.7e-08 vs 0.0005 (2.7e-08 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.0001, cap 40 | 3e-08 vs 0.00091 (0.023 vs 0.044) | 1.6e-09 vs 0.00047 (0.013 vs 0.018) | 1.9e-10 vs 0.00027 (0.047 vs 0.057) | 1.5e-10 vs 2.7e-05 (4.9e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.1e-08 vs 1.8e-08) | 9.5e-09 vs 0.0005 (9.5e-09 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 10 | 0.0016 vs 0.00091 (0.039 vs 0.044) | 0.0013 vs 0.00047 (0.019 vs 0.018) | 0.001 vs 0.00027 (0.061 vs 0.057) | 0.00011 vs 2.7e-05 (0.0011 vs 0.00034) | 5.7e-06 vs 6.4e-07 (5.7e-06 vs 6.4e-07) | 2.8e-07 vs 4.7e-11 (3.9e-06 vs 1.8e-08) | 0.00076 vs 0.0005 (0.00076 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 20 | 0.00068 vs 0.00091 (0.059 vs 0.044) | 0.00036 vs 0.00047 (0.026 vs 0.018) | 0.00023 vs 0.00027 (0.086 vs 0.057) | 2.2e-05 vs 2.7e-05 (0.00071 vs 0.00034) | 6.2e-07 vs 6.4e-07 (6.2e-07 vs 6.4e-07) | 1.5e-08 vs 4.7e-11 (6.9e-07 vs 1.8e-08) | 0.00032 vs 0.0005 (0.00032 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 30 | 0.00056 vs 0.00091 (0.067 vs 0.044) | 0.00031 vs 0.00047 (0.029 vs 0.018) | 0.00021 vs 0.00027 (0.096 vs 0.057) | 1.9e-05 vs 2.7e-05 (0.00062 vs 0.00034) | 6.1e-07 vs 6.4e-07 (6.1e-07 vs 6.4e-07) | 1.5e-08 vs 4.7e-11 (5.9e-07 vs 1.8e-08) | 0.00024 vs 0.0005 (0.00024 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 40 | 0.00021 vs 0.00091 (0.079 vs 0.044) | 8.4e-05 vs 0.00047 (0.033 vs 0.018) | 4.6e-05 vs 0.00027 (0.1 vs 0.057) | 4.2e-06 vs 2.7e-05 (0.00049 vs 0.00034) | 2.8e-08 vs 6.4e-07 (2.8e-08 vs 6.4e-07) | 8.8e-10 vs 4.7e-11 (1.5e-07 vs 1.8e-08) | 0.0001 vs 0.0005 (0.0001 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 10 | 0.00049 vs 0.00091 (0.018 vs 0.044) | 0.00029 vs 0.00047 (0.008 vs 0.018) | 0.0002 vs 0.00027 (0.034 vs 0.057) | 1.8e-05 vs 2.7e-05 (0.00035 vs 0.00034) | 6.1e-07 vs 6.4e-07 (6.1e-07 vs 6.4e-07) | 1.5e-08 vs 4.7e-11 (5.6e-07 vs 1.8e-08) | 0.0002 vs 0.0005 (0.0002 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 20 | 0.00014 vs 0.00091 (0.036 vs 0.044) | 6.7e-05 vs 0.00047 (0.015 vs 0.018) | 3.9e-05 vs 0.00027 (0.061 vs 0.057) | 3.5e-06 vs 2.7e-05 (0.00024 vs 0.00034) | 2.7e-08 vs 6.4e-07 (2.7e-08 vs 6.4e-07) | 8.6e-10 vs 4.7e-11 (1.2e-07 vs 1.8e-08) | 7e-05 vs 0.0005 (7e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 30 | 5.8e-05 vs 0.00091 (0.052 vs 0.044) | 1.9e-05 vs 0.00047 (0.021 vs 0.018) | 9.1e-06 vs 0.00027 (0.082 vs 0.057) | 7e-07 vs 2.7e-05 (0.0002 vs 0.00034) | 2.9e-09 vs 6.4e-07 (2.9e-09 vs 6.4e-07) | 4.6e-11 vs 4.7e-11 (3.2e-08 vs 1.8e-08) | 2.8e-05 vs 0.0005 (2.8e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 40 | 4.7e-05 vs 0.00091 (0.061 vs 0.044) | 1.6e-05 vs 0.00047 (0.023 vs 0.018) | 7.9e-06 vs 0.00027 (0.092 vs 0.057) | 5.9e-07 vs 2.7e-05 (0.0002 vs 0.00034) | 2.9e-09 vs 6.4e-07 (2.9e-09 vs 6.4e-07) | 4.5e-11 vs 4.7e-11 (2.6e-08 vs 1.8e-08) | 2.1e-05 vs 0.0005 (2.1e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 10 | 0.00012 vs 0.00091 (0.012 vs 0.044) | 6.2e-05 vs 0.00047 (0.005 vs 0.018) | 3.7e-05 vs 0.00027 (0.024 vs 0.057) | 3.3e-06 vs 2.7e-05 (0.00014 vs 0.00034) | 2.7e-08 vs 6.4e-07 (2.7e-08 vs 6.4e-07) | 8.6e-10 vs 4.7e-11 (1.1e-07 vs 1.8e-08) | 5.6e-05 vs 0.0005 (5.6e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 20 | 4.6e-05 vs 0.00091 (0.028 vs 0.044) | 1.6e-05 vs 0.00047 (0.011 vs 0.018) | 7.8e-06 vs 0.00027 (0.051 vs 0.057) | 5.8e-07 vs 2.7e-05 (0.00011 vs 0.00034) | 2.9e-09 vs 6.4e-07 (2.9e-09 vs 6.4e-07) | 4.5e-11 vs 4.7e-11 (2.4e-08 vs 1.8e-08) | 2e-05 vs 0.0005 (2e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 30 | 1.6e-05 vs 0.00091 (0.04 vs 0.044) | 4.4e-06 vs 0.00047 (0.016 vs 0.018) | 1.8e-06 vs 0.00027 (0.069 vs 0.057) | 1.3e-07 vs 2.7e-05 (0.0001 vs 0.00034) | 1.3e-10 vs 6.4e-07 (1.3e-10 vs 6.4e-07) | 2.8e-12 vs 4.7e-11 (8.6e-09 vs 1.8e-08) | 8.3e-06 vs 0.0005 (8.3e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 40 | 1.2e-05 vs 0.00091 (0.051 vs 0.044) | 3.5e-06 vs 0.00047 (0.019 vs 0.018) | 1.5e-06 vs 0.00027 (0.083 vs 0.057) | 1.1e-07 vs 2.7e-05 (0.00011 vs 0.00034) | 1.2e-10 vs 6.4e-07 (1.2e-10 vs 6.4e-07) | 2.7e-12 vs 4.7e-11 (7e-09 vs 1.8e-08) | 6.1e-06 vs 0.0005 (6.1e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 10 | 3.8e-05 vs 0.00091 (0.0088 vs 0.044) | 1.5e-05 vs 0.00047 (0.0034 vs 0.018) | 7.5e-06 vs 0.00027 (0.02 vs 0.057) | 5.6e-07 vs 2.7e-05 (5.6e-05 vs 0.00034) | 2.8e-09 vs 6.4e-07 (2.8e-09 vs 6.4e-07) | 4.5e-11 vs 4.7e-11 (2.1e-08 vs 1.8e-08) | 1.6e-05 vs 0.0005 (1.6e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 20 | 1.2e-05 vs 0.00091 (0.018 vs 0.044) | 3.5e-06 vs 0.00047 (0.0074 vs 0.018) | 1.5e-06 vs 0.00027 (0.038 vs 0.057) | 1.1e-07 vs 2.7e-05 (5.1e-05 vs 0.00034) | 1.2e-10 vs 6.4e-07 (1.2e-10 vs 6.4e-07) | 2.7e-12 vs 4.7e-11 (6.5e-09 vs 1.8e-08) | 5.9e-06 vs 0.0005 (5.9e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 30 | 3.9e-06 vs 0.00091 (0.033 vs 0.044) | 8.5e-07 vs 0.00047 (0.013 vs 0.018) | 3e-07 vs 0.00027 (0.061 vs 0.057) | 1.9e-08 vs 2.7e-05 (5.2e-05 vs 0.00034) | 1.3e-11 vs 6.4e-07 (1.3e-11 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.9e-09 vs 1.8e-08) | 1.9e-06 vs 0.0005 (1.9e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 40 | 3.8e-06 vs 0.00091 (0.041 vs 0.044) | 8.4e-07 vs 0.00047 (0.016 vs 0.018) | 3e-07 vs 0.00027 (0.073 vs 0.057) | 1.8e-08 vs 2.7e-05 (5.8e-05 vs 0.00034) | 1.3e-11 vs 6.4e-07 (1.3e-11 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.9e-09 vs 1.8e-08) | 1.8e-06 vs 0.0005 (1.8e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 10 | 9.3e-06 vs 0.00091 (0.0062 vs 0.044) | 3.2e-06 vs 0.00047 (0.0024 vs 0.018) | 1.4e-06 vs 0.00027 (0.015 vs 0.057) | 1e-07 vs 2.7e-05 (2.6e-05 vs 0.00034) | 1.2e-10 vs 6.4e-07 (1.2e-10 vs 6.4e-07) | 2.7e-12 vs 4.7e-11 (5.3e-09 vs 1.8e-08) | 4.6e-06 vs 0.0005 (4.6e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 20 | 4.7e-06 vs 0.00091 (0.016 vs 0.044) | 1e-06 vs 0.00047 (0.0064 vs 0.018) | 3.6e-07 vs 0.00027 (0.034 vs 0.057) | 2.3e-08 vs 2.7e-05 (3.3e-05 vs 0.00034) | 1.4e-11 vs 6.4e-07 (1.4e-11 vs 6.4e-07) | <1e-12 vs 4.7e-11 (2.3e-09 vs 1.8e-08) | 2.4e-06 vs 0.0005 (2.4e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 30 | 1e-06 vs 0.00091 (0.025 vs 0.044) | 1.8e-07 vs 0.00047 (0.01 vs 0.018) | 5.7e-08 vs 0.00027 (0.05 vs 0.057) | 3.5e-09 vs 2.7e-05 (2.9e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (6.7e-10 vs 1.8e-08) | 5.4e-07 vs 0.0005 (5.4e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 40 | 9.9e-07 vs 0.00091 (0.037 vs 0.044) | 1.8e-07 vs 0.00047 (0.014 vs 0.018) | 5.7e-08 vs 0.00027 (0.067 vs 0.057) | 3.5e-09 vs 2.7e-05 (3.9e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (6.8e-10 vs 1.8e-08) | 5.3e-07 vs 0.0005 (5.3e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 10 | 9.3e-06 vs 0.00091 (0.0062 vs 0.044) | 3.2e-06 vs 0.00047 (0.0024 vs 0.018) | 1.4e-06 vs 0.00027 (0.015 vs 0.057) | 1e-07 vs 2.7e-05 (2.6e-05 vs 0.00034) | 1.2e-10 vs 6.4e-07 (1.2e-10 vs 6.4e-07) | 2.7e-12 vs 4.7e-11 (5.3e-09 vs 1.8e-08) | 4.6e-06 vs 0.0005 (4.6e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 20 | 9.5e-07 vs 0.00091 (0.012 vs 0.044) | 1.8e-07 vs 0.00047 (0.0049 vs 0.018) | 5.6e-08 vs 0.00027 (0.029 vs 0.057) | 3.5e-09 vs 2.7e-05 (1.5e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (5.6e-10 vs 1.8e-08) | 5e-07 vs 0.0005 (5e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 30 | 9.7e-07 vs 0.00091 (0.023 vs 0.044) | 1.8e-07 vs 0.00047 (0.0092 vs 0.018) | 5.6e-08 vs 0.00027 (0.047 vs 0.057) | 3.5e-09 vs 2.7e-05 (2.4e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (6.1e-10 vs 1.8e-08) | 5.2e-07 vs 0.0005 (5.2e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 40 | 9e-07 vs 0.00091 (0.031 vs 0.044) | 1.8e-07 vs 0.00047 (0.012 vs 0.018) | 5.6e-08 vs 0.00027 (0.059 vs 0.057) | 3.4e-09 vs 2.7e-05 (2.7e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (5.7e-10 vs 1.8e-08) | 4.8e-07 vs 0.0005 (4.8e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 20 | 8e-07 vs 0.00091 (0.01 vs 0.044) | 1.7e-07 vs 0.00047 (0.0042 vs 0.018) | 5.3e-08 vs 0.00027 (0.026 vs 0.057) | 3.3e-09 vs 2.7e-05 (1.1e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (4.5e-10 vs 1.8e-08) | 4.1e-07 vs 0.0005 (4.1e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 30 | 3e-07 vs 0.00091 (0.019 vs 0.044) | 4.3e-08 vs 0.00047 (0.008 vs 0.018) | 1.1e-08 vs 0.00027 (0.042 vs 0.057) | 5.8e-10 vs 2.7e-05 (1.4e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.9e-10 vs 1.8e-08) | 1.4e-07 vs 0.0005 (1.4e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 40 | 2.9e-07 vs 0.00091 (0.026 vs 0.044) | 4.3e-08 vs 0.00047 (0.01 vs 0.018) | 1.1e-08 vs 0.00027 (0.052 vs 0.057) | 5.8e-10 vs 2.7e-05 (1.6e-05 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.8e-10 vs 1.8e-08) | 1.4e-07 vs 0.0005 (1.4e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.0001, cap 20 | 2e-08 vs 0.00091 (0.0032 vs 0.044) | 2e-09 vs 0.00047 (0.0014 vs 0.018) | 4e-10 vs 0.00027 (0.013 vs 0.057) | 1.7e-11 vs 2.7e-05 (1.4e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.5e-11 vs 1.8e-08) | 9.7e-09 vs 0.0005 (9.7e-09 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.0001, cap 30 | 5.9e-09 vs 0.00091 (0.0068 vs 0.044) | 4.7e-10 vs 0.00047 (0.0032 vs 0.018) | 8e-11 vs 0.00027 (0.021 vs 0.057) | 3.4e-12 vs 2.7e-05 (2e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1e-11 vs 1.8e-08) | 3.4e-09 vs 0.0005 (3.4e-09 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.0001, cap 40 | 2e-09 vs 0.00091 (0.013 vs 0.044) | 1.1e-10 vs 0.00047 (0.0058 vs 0.018) | 1.6e-11 vs 0.00027 (0.031 vs 0.057) | <1e-12 vs 2.7e-05 (2.6e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (6.2e-12 vs 1.8e-08) | 1e-09 vs 0.0005 (1e-09 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 10 | 0.0008 vs 0.00091 (0.025 vs 0.044) | 0.00089 vs 0.00047 (0.01 vs 0.018) | 0.00075 vs 0.00027 (0.038 vs 0.057) | 6e-05 vs 2.7e-05 (0.00026 vs 0.00034) | 3.8e-06 vs 6.4e-07 (3.8e-06 vs 6.4e-07) | 4.4e-09 vs 4.7e-11 (1.3e-07 vs 1.8e-08) | 0.00034 vs 0.0005 (0.00034 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 20 | 0.00027 vs 0.00091 (0.036 vs 0.044) | 0.00021 vs 0.00047 (0.014 vs 0.018) | 0.00015 vs 0.00027 (0.051 vs 0.057) | 1e-05 vs 2.7e-05 (0.00012 vs 0.00034) | 4.1e-07 vs 6.4e-07 (4.1e-07 vs 6.4e-07) | 1.1e-10 vs 4.7e-11 (1.1e-08 vs 1.8e-08) | 0.00012 vs 0.0005 (0.00012 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 30 | 0.00023 vs 0.00091 (0.041 vs 0.044) | 0.00019 vs 0.00047 (0.015 vs 0.018) | 0.00013 vs 0.00027 (0.056 vs 0.057) | 8.8e-06 vs 2.7e-05 (0.0001 vs 0.00034) | 4e-07 vs 6.4e-07 (4e-07 vs 6.4e-07) | 1e-10 vs 4.7e-11 (1.1e-08 vs 1.8e-08) | 9.5e-05 vs 0.0005 (9.5e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 40 | 7e-05 vs 0.00091 (0.048 vs 0.044) | 4.4e-05 vs 0.00047 (0.017 vs 0.018) | 2.8e-05 vs 0.00027 (0.063 vs 0.057) | 1.7e-06 vs 2.7e-05 (6.2e-05 vs 0.00034) | 1.8e-08 vs 6.4e-07 (1.8e-08 vs 6.4e-07) | 3e-12 vs 4.7e-11 (1.3e-09 vs 1.8e-08) | 3.6e-05 vs 0.0005 (3.6e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 10 | 0.00021 vs 0.00091 (0.011 vs 0.044) | 0.00018 vs 0.00047 (0.0042 vs 0.018) | 0.00013 vs 0.00027 (0.021 vs 0.057) | 8.6e-06 vs 2.7e-05 (7e-05 vs 0.00034) | 4e-07 vs 6.4e-07 (4e-07 vs 6.4e-07) | 1e-10 vs 4.7e-11 (1e-08 vs 1.8e-08) | 8.1e-05 vs 0.0005 (8.1e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 20 | 5.1e-05 vs 0.00091 (0.021 vs 0.044) | 3.7e-05 vs 0.00047 (0.0077 vs 0.018) | 2.5e-05 vs 0.00027 (0.035 vs 0.057) | 1.5e-06 vs 2.7e-05 (3.4e-05 vs 0.00034) | 1.7e-08 vs 6.4e-07 (1.7e-08 vs 6.4e-07) | 3e-12 vs 4.7e-11 (1.2e-09 vs 1.8e-08) | 2.5e-05 vs 0.0005 (2.5e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 30 | 1.8e-05 vs 0.00091 (0.031 vs 0.044) | 9e-06 vs 0.00047 (0.011 vs 0.018) | 4.9e-06 vs 0.00027 (0.046 vs 0.057) | 2.5e-07 vs 2.7e-05 (2.3e-05 vs 0.00034) | 1.9e-09 vs 6.4e-07 (1.9e-09 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.6e-10 vs 1.8e-08) | 8.9e-06 vs 0.0005 (8.9e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 40 | 1.4e-05 vs 0.00091 (0.036 vs 0.044) | 7.7e-06 vs 0.00047 (0.012 vs 0.018) | 4.2e-06 vs 0.00027 (0.051 vs 0.057) | 2.2e-07 vs 2.7e-05 (2.1e-05 vs 0.00034) | 1.9e-09 vs 6.4e-07 (1.9e-09 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.4e-10 vs 1.8e-08) | 6.7e-06 vs 0.0005 (6.7e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 10 | 4.6e-05 vs 0.00091 (0.0072 vs 0.044) | 3.5e-05 vs 0.00047 (0.0025 vs 0.018) | 2.4e-05 vs 0.00027 (0.014 vs 0.057) | 1.4e-06 vs 2.7e-05 (2.3e-05 vs 0.00034) | 1.7e-08 vs 6.4e-07 (1.7e-08 vs 6.4e-07) | 3e-12 vs 4.7e-11 (1.2e-09 vs 1.8e-08) | 2.1e-05 vs 0.0005 (2.1e-05 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 20 | 1.4e-05 vs 0.00091 (0.016 vs 0.044) | 7.7e-06 vs 0.00047 (0.0056 vs 0.018) | 4.2e-06 vs 0.00027 (0.029 vs 0.057) | 2.2e-07 vs 2.7e-05 (1.3e-05 vs 0.00034) | 1.9e-09 vs 6.4e-07 (1.9e-09 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.4e-10 vs 1.8e-08) | 6.6e-06 vs 0.0005 (6.6e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 30 | 4.3e-06 vs 0.00091 (0.023 vs 0.044) | 1.8e-06 vs 0.00047 (0.0082 vs 0.018) | 9.2e-07 vs 0.00027 (0.037 vs 0.057) | 4.2e-08 vs 2.7e-05 (1e-05 vs 0.00034) | 8.6e-11 vs 6.4e-07 (8.6e-11 vs 6.4e-07) | <1e-12 vs 4.7e-11 (2.7e-11 vs 1.8e-08) | 2.4e-06 vs 0.0005 (2.4e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 40 | 3.2e-06 vs 0.00091 (0.029 vs 0.044) | 1.5e-06 vs 0.00047 (0.01 vs 0.018) | 8e-07 vs 0.00027 (0.044 vs 0.057) | 3.6e-08 vs 2.7e-05 (9.8e-06 vs 0.00034) | 8.2e-11 vs 6.4e-07 (8.2e-11 vs 6.4e-07) | <1e-12 vs 4.7e-11 (2.3e-11 vs 1.8e-08) | 1.8e-06 vs 0.0005 (1.8e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 10 | 1.3e-05 vs 0.00091 (0.0051 vs 0.044) | 7.3e-06 vs 0.00047 (0.0017 vs 0.018) | 4.1e-06 vs 0.00027 (0.012 vs 0.057) | 2.1e-07 vs 2.7e-05 (8.1e-06 vs 0.00034) | 1.9e-09 vs 6.4e-07 (1.9e-09 vs 6.4e-07) | <1e-12 vs 4.7e-11 (1.4e-10 vs 1.8e-08) | 5.5e-06 vs 0.0005 (5.5e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 20 | 3.2e-06 vs 0.00091 (0.01 vs 0.044) | 1.5e-06 vs 0.00047 (0.0036 vs 0.018) | 8e-07 vs 0.00027 (0.022 vs 0.057) | 3.6e-08 vs 2.7e-05 (5.5e-06 vs 0.00034) | 8.2e-11 vs 6.4e-07 (8.2e-11 vs 6.4e-07) | <1e-12 vs 4.7e-11 (2.3e-11 vs 1.8e-08) | 1.7e-06 vs 0.0005 (1.7e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 30 | 9.1e-07 vs 0.00091 (0.019 vs 0.044) | 3.1e-07 vs 0.00047 (0.0066 vs 0.018) | 1.4e-07 vs 0.00027 (0.032 vs 0.057) | 5.3e-09 vs 2.7e-05 (4.5e-06 vs 0.00034) | 8.7e-12 vs 6.4e-07 (8.7e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (3.8e-12 vs 1.8e-08) | 4.8e-07 vs 0.0005 (4.8e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 40 | 9e-07 vs 0.00091 (0.024 vs 0.044) | 3.1e-07 vs 0.00047 (0.0083 vs 0.018) | 1.4e-07 vs 0.00027 (0.038 vs 0.057) | 5.3e-09 vs 2.7e-05 (4.9e-06 vs 0.00034) | 8.7e-12 vs 6.4e-07 (8.7e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (3.8e-12 vs 1.8e-08) | 4.7e-07 vs 0.0005 (4.7e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 10 | 2.8e-06 vs 0.00091 (0.0035 vs 0.044) | 1.4e-06 vs 0.00047 (0.0012 vs 0.018) | 7.6e-07 vs 0.00027 (0.0093 vs 0.057) | 3.5e-08 vs 2.7e-05 (3.1e-06 vs 0.00034) | 8.1e-11 vs 6.4e-07 (8.1e-11 vs 6.4e-07) | <1e-12 vs 4.7e-11 (2.2e-11 vs 1.8e-08) | 1.4e-06 vs 0.0005 (1.4e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 20 | 1.1e-06 vs 0.00091 (0.0088 vs 0.044) | 3.8e-07 vs 0.00047 (0.0031 vs 0.018) | 1.6e-07 vs 0.00027 (0.02 vs 0.057) | 6.3e-09 vs 2.7e-05 (3.3e-06 vs 0.00034) | 8.9e-12 vs 6.4e-07 (8.9e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (4.7e-12 vs 1.8e-08) | 6.3e-07 vs 0.0005 (6.3e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 30 | 2e-07 vs 0.00091 (0.014 vs 0.044) | 6.1e-08 vs 0.00047 (0.005 vs 0.018) | 2.6e-08 vs 0.00027 (0.027 vs 0.057) | 8.9e-10 vs 2.7e-05 (2.3e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 1.3e-07 vs 0.0005 (1.3e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 40 | 2e-07 vs 0.00091 (0.021 vs 0.044) | 6.1e-08 vs 0.00047 (0.0075 vs 0.018) | 2.6e-08 vs 0.00027 (0.034 vs 0.057) | 8.9e-10 vs 2.7e-05 (3e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 1.3e-07 vs 0.0005 (1.3e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 10 | 2.8e-06 vs 0.00091 (0.0035 vs 0.044) | 1.4e-06 vs 0.00047 (0.0012 vs 0.018) | 7.6e-07 vs 0.00027 (0.0093 vs 0.057) | 3.5e-08 vs 2.7e-05 (3.1e-06 vs 0.00034) | 8.1e-11 vs 6.4e-07 (8.1e-11 vs 6.4e-07) | <1e-12 vs 4.7e-11 (2.2e-11 vs 1.8e-08) | 1.4e-06 vs 0.0005 (1.4e-06 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 20 | 2e-07 vs 0.00091 (0.0066 vs 0.044) | 6e-08 vs 0.00047 (0.0023 vs 0.018) | 2.6e-08 vs 0.00027 (0.018 vs 0.057) | 8.9e-10 vs 2.7e-05 (1.3e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 1.2e-07 vs 0.0005 (1.2e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 30 | 2e-07 vs 0.00091 (0.013 vs 0.044) | 6e-08 vs 0.00047 (0.0046 vs 0.018) | 2.6e-08 vs 0.00027 (0.025 vs 0.057) | 8.9e-10 vs 2.7e-05 (1.9e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 1.2e-07 vs 0.0005 (1.2e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 40 | 1.9e-07 vs 0.00091 (0.017 vs 0.044) | 6e-08 vs 0.00047 (0.0063 vs 0.018) | 2.6e-08 vs 0.00027 (0.03 vs 0.057) | 8.8e-10 vs 2.7e-05 (2.1e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 1.2e-07 vs 0.0005 (1.2e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 20 | 1.8e-07 vs 0.00091 (0.0056 vs 0.044) | 5.7e-08 vs 0.00047 (0.002 vs 0.018) | 2.5e-08 vs 0.00027 (0.016 vs 0.057) | 8.5e-10 vs 2.7e-05 (9.7e-07 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 1e-07 vs 0.0005 (1e-07 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 30 | 5.4e-08 vs 0.00091 (0.011 vs 0.044) | 1.2e-08 vs 0.00047 (0.0039 vs 0.018) | 4.4e-09 vs 0.00027 (0.023 vs 0.057) | 1.3e-10 vs 2.7e-05 (1e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 3.1e-08 vs 0.0005 (3.1e-08 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 40 | 5.4e-08 vs 0.00091 (0.014 vs 0.044) | 1.2e-08 vs 0.00047 (0.0053 vs 0.018) | 4.4e-09 vs 0.00027 (0.027 vs 0.057) | 1.3e-10 vs 2.7e-05 (1.1e-06 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 3.1e-08 vs 0.0005 (3.1e-08 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.0001, cap 20 | 2.9e-09 vs 0.00091 (0.0017 vs 0.044) | 4.7e-10 vs 0.00047 (0.00061 vs 0.018) | 1.4e-10 vs 0.00027 (0.0086 vs 0.057) | 3e-12 vs 2.7e-05 (9.8e-08 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 1.8e-09 vs 0.0005 (1.8e-09 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.0001, cap 30 | 7.3e-10 vs 0.00091 (0.0036 vs 0.044) | 9.8e-11 vs 0.00047 (0.0014 vs 0.018) | 2.7e-11 vs 0.00027 (0.014 vs 0.057) | <1e-12 vs 2.7e-05 (1.3e-07 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 5.7e-10 vs 0.0005 (5.7e-10 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.0001, cap 40 | 2.1e-10 vs 0.00091 (0.0068 vs 0.044) | 2.1e-11 vs 0.00047 (0.0026 vs 0.018) | 4.7e-12 vs 0.00027 (0.018 vs 0.057) | <1e-12 vs 2.7e-05 (1.5e-07 vs 0.00034) | <1e-12 vs 6.4e-07 (<1e-12 vs 6.4e-07) | <1e-12 vs 4.7e-11 (<1e-12 vs 1.8e-08) | 1.5e-10 vs 0.0005 (1.5e-10 vs 0.0005) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |

Per group, the current rule against delta 0.02, alpha 0.01, cap 20, delta 0.03, alpha 0.003, cap 20: the false-switch rate at gain 0 (m equal challengers; in brackets, with the group's contest effect added), and the power at 5% and 10%:

| group | current: rate (contest effect) | 5% | 10% | d 0.02 a 0.01 c 20: rate (contest effect) | 5% | 10% | d 0.03 a 0.003 c 20: rate (contest effect) | 5% | 10% |
|---|---|---|---|---|---|---|---|---|---|
| dev2-replay | 0.00091 (0.044) | 0.068 | 0.641 | 0.00095 (0.071) | 0.142 | 0.681 | 2.7e-05 (0.027) | 0.032 | 0.427 |
| dev2-ladder | 0.00047 (0.018) | 0.061 | 0.723 | 0.00026 (0.047) | 0.183 | 0.812 | 5.2e-06 (0.014) | 0.018 | 0.609 |
| dev2-replay-solo | 0.00027 (0.057) | 0.023 | 0.570 | 0.00026 (0.09) | 0.087 | 0.909 | 1.8e-06 (0.048) | 0.014 | 0.647 |
| dev2-ladder-lowload | 2.7e-05 (0.00034) | 0.043 | 0.961 | 6.7e-05 (0.004) | 0.287 | 1.000 | 7.8e-07 (0.00032) | 0.059 | 0.960 |
| dev2-replay-solo-lowload | 6.4e-07 (6.4e-07) | 0.074 | 0.986 | 8.7e-07 (8.7e-07) | 0.910 | 1.000 | 4.6e-10 (4.6e-10) | 0.765 | 0.982 |
| dev1-replay | 4.7e-11 (1.8e-08) | 0.059 | 0.998 | 1.9e-06 (0.00017) | 0.871 | 1.000 | 9.6e-11 (5.4e-07) | 0.352 | 0.999 |
| dev1-ladder | 0.0005 (0.0005) | 0.073 | 0.724 | 0.00028 (0.00028) | 0.140 | 0.827 | 1.1e-05 (1.1e-05) | 0.034 | 0.550 |
| dev1-replay-solo | <1e-12 (<1e-12) | 0.052 | 0.998 | <1e-12 (<1e-12) | 0.998 | 0.998 | <1e-12 (<1e-12) | 0.985 | 0.986 |

## The null

### dev2-replay: 3911 rounds, 523 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.1700 | 0.0771 | -0.0096 | -1.013 | -0.527 | -0.281 | +0.250 | +0.487 | +0.954 | 0.273 (1067) [0.259, 0.287] | 0.524 |

- Load (1-min) 11.1-20.9, median 19.6; the preference's time per round 6.2e-04-0.0862 s, median 0.00567.
- Order: mean x -0.0189 with the A/A arm after the preference (2193 rounds), +0.0024 before it (1718).
- Successive rounds: lag-1 correlation 0.048; contest means vary 1.23x what independent rounds give (523 contests): a contest effect of sd 0.0396.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.1694 (523), q15=0 0.1828 (483), n=4096 0.1472 (297), n=4096,q15=0 0.2451 (14), q15=1 0.3827 (3).
- Distinct challengers per round (most common): 2.

### dev2-ladder: 291 rounds, 32 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.1779 | 0.0704 | -0.0063 | -0.710 | -0.532 | -0.280 | +0.206 | +0.695 | +0.930 | 0.261 (76) [0.212, 0.316] | 0.515 |

- Load (1-min) 16.9-37.7, median 24.5; the preference's time per round 0.0144-0.0797 s, median 0.0231.
- Order: mean x -0.0072 with the A/A arm after the preference (160 rounds), -0.0052 before it (131).
- Successive rounds: lag-1 correlation 0.145; contest means vary 1.06x what independent rounds give (32 contests): a contest effect of sd 0.0318.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.2335 (32), q15=0 0.2104 (32), n=4096 0.1813 (28).
- Distinct challengers per round (most common): 2.

### dev2-replay-solo: 334 rounds, 97 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.1320 | 0.0861 | -0.0170 | -0.613 | -0.356 | -0.218 | +0.169 | +0.313 | +0.706 | 0.356 (119) [0.305, 0.41] | 0.563 |

- Load (1-min) 12.6-29.7, median 15.6; the preference's time per round 5.6e-04-0.0401 s, median 0.00363.
- Order: mean x -0.0269 with the A/A arm after the preference (213 rounds), +0.0003 before it (121).
- Successive rounds: lag-1 correlation 0.123; contest means vary 1.55x what independent rounds give (97 contests): a contest effect of sd 0.0508.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.1240 (97), q15=0 0.1312 (85), n=4096 0.1576 (61), n=4096,q15=0 0.1291 (4), q15=1 0.0633 (2).
- Distinct challengers per round (most common): 2.

### dev2-ladder-lowload: 174 rounds, 26 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0505 | 0.0442 | -0.0082 | -0.176 | -0.151 | -0.097 | +0.059 | +0.090 | +0.126 | 0.19 (33) [0.134, 0.256] | 0.517 |

- Load (1-min) 4.9-8.2, median 5.8; the preference's time per round 0.0114-0.0228 s, median 0.0178.
- Order: mean x -0.0135 with the A/A arm after the preference (100 rounds), -0.0010 before it (74).
- Successive rounds: lag-1 correlation 0.100; contest means vary 1.32x what independent rounds give (26 contests): a contest effect of sd 0.0143.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0460 (26), n=4096 0.0581 (26), q15=0 0.0400 (26).
- Distinct challengers per round (most common): 2.

### dev2-replay-solo-lowload: 315 rounds, 95 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0737 | 0.0317 | -0.0176 | -0.275 | -0.208 | -0.138 | +0.102 | +0.209 | +0.365 | 0.232 (73) [0.186, 0.282] | 0.654 |

- Load (1-min) 3.2-6.8, median 6.2; the preference's time per round 4.9e-04-0.0261 s, median 0.0026.
- Order: mean x -0.0281 with the A/A arm after the preference (204 rounds), +0.0016 before it (111).
- Successive rounds: lag-1 correlation 0.091; contest means vary 0.98x what independent rounds give (95 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0752 (95), q15=0 0.0721 (88), n=4096 0.0636 (72), n=4096,q15=0 0.1871 (3).
- Distinct challengers per round (most common): 2.

### dev1-replay: 3610 rounds, 497 contests (gravity-dev1)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0302 | 0.0240 | -0.0009 | -0.166 | -0.079 | -0.047 | +0.045 | +0.081 | +0.143 | 0.0368 (133) [0.0309, 0.0435] | 0.516 |

- Load (1-min) 1.4-8.1, median 7.2; the preference's time per round 0.00111-0.0502 s, median 0.00961.
- Order: mean x +0.0009 with the A/A arm after the preference (2052 rounds), -0.0033 before it (1558).
- Successive rounds: lag-1 correlation 0.076; contest means vary 1.19x what independent rounds give (497 contests): a contest effect of sd 0.0071.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0310 (497), q15=0 0.0622 (482), n=4096 0.0329 (404).
- Distinct challengers per round (most common): 2.

### dev1-ladder: 576 rounds, 64 contests (gravity-dev1)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0847 | 0.0640 | -0.0069 | -0.379 | -0.257 | -0.142 | +0.126 | +0.205 | +0.297 | 0.247 (142) [0.212, 0.284] | 0.533 |

- Load (1-min) 6.8-8.2, median 8.1; the preference's time per round 0.0285-0.089 s, median 0.0505.
- Order: mean x -0.0091 with the A/A arm after the preference (320 rounds), -0.0041 before it (256).
- Successive rounds: lag-1 correlation -0.011; contest means vary 0.54x what independent rounds give (64 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0788 (64), n=4096 0.1596 (64), q15=0 0.0775 (64).
- Distinct challengers per round (most common): 2.

### dev1-replay-solo: 283 rounds, 89 contests (gravity-dev1)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0244 | 0.0077 | -0.0013 | -0.047 | -0.039 | -0.020 | +0.012 | +0.038 | +0.274 | 0 (0) [0, 0.013] | 0.611 |

- Load (1-min) 1.2-7.2, median 1.9; the preference's time per round 0.00101-0.0328 s, median 0.00645.
- Order: mean x -0.0019 with the A/A arm after the preference (186 rounds), -0.0002 before it (97).
- Successive rounds: lag-1 correlation -0.118; contest means vary 0.80x what independent rounds give (89 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0255 (89), q15=0 0.0171 (85), n=4096 0.0274 (73), n=4096,q15=0 0.0694 (1).
- Distinct challengers per round (most common): 2.

## Dependence on load, work and place in the contest

### dev2-replay

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 11.1-18.5 | 761 | 0.2125 | 0.0916 | 0.306 |
| load (1-min) | 18.5-19.5 | 787 | 0.1596 | 0.0857 | 0.292 |
| load (1-min) | 19.5-19.8 | 788 | 0.1257 | 0.0639 | 0.228 |
| load (1-min) | 19.8-20.4 | 730 | 0.1652 | 0.0790 | 0.27 |
| load (1-min) | 20.4-20.9 | 845 | 0.1764 | 0.0696 | 0.269 |
| preference's time (s) | 6.2e-04-0.00261 | 782 | 0.1153 | 0.0641 | 0.223 |
| preference's time (s) | 0.00261-0.0041 | 782 | 0.1346 | 0.0713 | 0.253 |
| preference's time (s) | 0.0041-0.00743 | 783 | 0.1711 | 0.0685 | 0.262 |
| preference's time (s) | 0.00743-0.0123 | 781 | 0.1749 | 0.0763 | 0.256 |
| preference's time (s) | 0.0123-0.0862 | 783 | 0.2282 | 0.1146 | 0.37 |
| timed runs in the round | 2.5-3.5 | 528 | 0.1791 | 0.0625 | 0.214 |
| timed runs in the round | 3.5-4.5 | 3359 | 0.1690 | 0.0790 | 0.282 |
| timed runs in the round | 4.5-99 | 24 | 0.0823 | 0.0841 | 0.333 |
| round of the contest | 1-2 | 523 | 0.1963 | 0.0963 | 0.388 |
| round of the contest | 2-4 | 1046 | 0.1731 | 0.0782 | 0.267 |
| round of the contest | 4-6 | 376 | 0.1770 | 0.0667 | 0.221 |
| round of the contest | 6-11 | 546 | 0.1624 | 0.0738 | 0.262 |
| round of the contest | 11-21 | 1080 | 0.1506 | 0.0713 | 0.251 |
| round of the contest | 21-1e+03 | 340 | 0.1785 | 0.0714 | 0.259 |

### dev2-ladder

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 16.9-21.6 | 57 | 0.1717 | 0.1040 | 0.298 |
| load (1-min) | 21.6-23.2 | 58 | 0.2035 | 0.0729 | 0.224 |
| load (1-min) | 23.2-25 | 49 | 0.0800 | 0.0555 | 0.204 |
| load (1-min) | 25-28.8 | 65 | 0.1543 | 0.0633 | 0.231 |
| load (1-min) | 28.8-37.7 | 62 | 0.2323 | 0.0711 | 0.339 |
| preference's time (s) | 0.0144-0.0191 | 58 | 0.0630 | 0.0386 | 0.069 |
| preference's time (s) | 0.0191-0.0222 | 58 | 0.0969 | 0.0577 | 0.172 |
| preference's time (s) | 0.0222-0.0248 | 59 | 0.1582 | 0.0722 | 0.22 |
| preference's time (s) | 0.0248-0.0309 | 57 | 0.1403 | 0.0764 | 0.316 |
| preference's time (s) | 0.0309-0.0797 | 59 | 0.2984 | 0.1876 | 0.525 |
| timed runs in the round | 3.5-4.5 | 289 | 0.1785 | 0.0705 | 0.263 |
| round of the contest | 1-2 | 32 | 0.2623 | 0.1085 | 0.406 |
| round of the contest | 2-4 | 64 | 0.2466 | 0.1098 | 0.375 |
| round of the contest | 4-6 | 11 | 0.3114 | 0.0947 | 0.0909 |
| round of the contest | 6-11 | 20 | 0.1117 | 0.0573 | 0.3 |
| round of the contest | 11-21 | 40 | 0.1405 | 0.0764 | 0.325 |
| round of the contest | 21-1e+03 | 124 | 0.0892 | 0.0486 | 0.153 |

### dev2-replay-solo

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 12.6-14.2 | 62 | 0.1239 | 0.1069 | 0.371 |
| load (1-min) | 14.2-15.1 | 72 | 0.1410 | 0.0642 | 0.361 |
| load (1-min) | 15.1-16.7 | 59 | 0.1124 | 0.0833 | 0.339 |
| load (1-min) | 16.7-21.4 | 72 | 0.1287 | 0.0692 | 0.306 |
| load (1-min) | 21.4-29.7 | 69 | 0.1447 | 0.1322 | 0.406 |
| preference's time (s) | 5.6e-04-0.00199 | 67 | 0.1045 | 0.0901 | 0.343 |
| preference's time (s) | 0.00199-0.00298 | 67 | 0.1165 | 0.0815 | 0.358 |
| preference's time (s) | 0.00298-0.00539 | 66 | 0.1095 | 0.0749 | 0.258 |
| preference's time (s) | 0.00539-0.0103 | 67 | 0.1292 | 0.0940 | 0.448 |
| preference's time (s) | 0.0103-0.0401 | 67 | 0.1839 | 0.1184 | 0.373 |
| timed runs in the round | 2.5-3.5 | 89 | 0.1036 | 0.0650 | 0.202 |
| timed runs in the round | 3.5-4.5 | 245 | 0.1407 | 0.0990 | 0.412 |
| round of the contest | 1-2 | 97 | 0.1456 | 0.0774 | 0.423 |
| round of the contest | 2-4 | 194 | 0.1265 | 0.0929 | 0.351 |
| round of the contest | 4-6 | 43 | 0.1248 | 0.0708 | 0.233 |

### dev2-ladder-lowload

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 4.87-5.55 | 34 | 0.0577 | 0.0536 | 0.235 |
| load (1-min) | 5.55-5.78 | 35 | 0.0647 | 0.0585 | 0.371 |
| load (1-min) | 5.78-5.9 | 23 | 0.0330 | 0.0298 | 0.0435 |
| load (1-min) | 5.9-6.93 | 47 | 0.0414 | 0.0456 | 0.128 |
| load (1-min) | 6.93-8.25 | 35 | 0.0440 | 0.0338 | 0.143 |
| preference's time (s) | 0.0114-0.0153 | 35 | 0.0524 | 0.0523 | 0.143 |
| preference's time (s) | 0.0153-0.0173 | 35 | 0.0580 | 0.0477 | 0.143 |
| preference's time (s) | 0.0173-0.0185 | 34 | 0.0345 | 0.0369 | 0.118 |
| preference's time (s) | 0.0185-0.0197 | 35 | 0.0416 | 0.0430 | 0.171 |
| preference's time (s) | 0.0197-0.0228 | 35 | 0.0565 | 0.0578 | 0.371 |
| timed runs in the round | 3.5-4.5 | 174 | 0.0505 | 0.0442 | 0.19 |
| round of the contest | 1-2 | 26 | 0.0466 | 0.0535 | 0.308 |
| round of the contest | 2-4 | 52 | 0.0487 | 0.0322 | 0.192 |
| round of the contest | 6-11 | 10 | 0.0656 | 0.0353 | 0.1 |
| round of the contest | 11-21 | 20 | 0.0352 | 0.0319 | 0.05 |
| round of the contest | 21-1e+03 | 62 | 0.0515 | 0.0514 | 0.21 |

### dev2-replay-solo-lowload

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 3.24-4.88 | 57 | 0.0683 | 0.0236 | 0.14 |
| load (1-min) | 4.88-5.92 | 54 | 0.0721 | 0.0631 | 0.278 |
| load (1-min) | 5.92-6.36 | 72 | 0.0861 | 0.0203 | 0.236 |
| load (1-min) | 6.36-6.76 | 56 | 0.0716 | 0.0337 | 0.214 |
| load (1-min) | 6.76-6.83 | 76 | 0.0669 | 0.0328 | 0.276 |
| preference's time (s) | 4.9e-04-0.00156 | 63 | 0.0759 | 0.0246 | 0.206 |
| preference's time (s) | 0.00156-0.00215 | 63 | 0.0595 | 0.0311 | 0.302 |
| preference's time (s) | 0.00215-0.00398 | 63 | 0.0526 | 0.0481 | 0.333 |
| preference's time (s) | 0.00398-0.00693 | 63 | 0.0824 | 0.0275 | 0.19 |
| preference's time (s) | 0.00693-0.0261 | 63 | 0.0851 | 0.0355 | 0.127 |
| timed runs in the round | 2.5-3.5 | 72 | 0.0421 | 0.0117 | 0.111 |
| timed runs in the round | 3.5-4.5 | 243 | 0.0802 | 0.0382 | 0.267 |
| round of the contest | 1-2 | 95 | 0.0847 | 0.0641 | 0.495 |
| round of the contest | 2-4 | 190 | 0.0679 | 0.0272 | 0.132 |
| round of the contest | 4-6 | 30 | 0.0241 | 0.0090 | 0.0333 |

### dev1-replay

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 1.38-7.12 | 690 | 0.0343 | 0.0272 | 0.0435 |
| load (1-min) | 7.12-7.21 | 744 | 0.0296 | 0.0254 | 0.0376 |
| load (1-min) | 7.21-7.27 | 729 | 0.0276 | 0.0235 | 0.0329 |
| load (1-min) | 7.27-7.41 | 506 | 0.0271 | 0.0237 | 0.0237 |
| load (1-min) | 7.41-8.07 | 941 | 0.0307 | 0.0232 | 0.0414 |
| preference's time (s) | 0.00111-0.00376 | 722 | 0.0301 | 0.0225 | 0.0485 |
| preference's time (s) | 0.00376-0.00646 | 722 | 0.0248 | 0.0209 | 0.0222 |
| preference's time (s) | 0.00646-0.013 | 722 | 0.0234 | 0.0219 | 0.0139 |
| preference's time (s) | 0.013-0.0201 | 722 | 0.0331 | 0.0244 | 0.0388 |
| preference's time (s) | 0.0201-0.0502 | 722 | 0.0368 | 0.0331 | 0.0609 |
| timed runs in the round | 2.5-3.5 | 265 | 0.0265 | 0.0210 | 0.0264 |
| timed runs in the round | 3.5-4.5 | 3345 | 0.0304 | 0.0243 | 0.0377 |
| round of the contest | 1-2 | 497 | 0.0367 | 0.0286 | 0.0765 |
| round of the contest | 2-4 | 994 | 0.0302 | 0.0230 | 0.0382 |
| round of the contest | 4-6 | 279 | 0.0259 | 0.0203 | 0.0143 |
| round of the contest | 6-11 | 540 | 0.0285 | 0.0216 | 0.0259 |
| round of the contest | 11-21 | 1080 | 0.0289 | 0.0253 | 0.0287 |
| round of the contest | 21-1e+03 | 220 | 0.0280 | 0.0244 | 0.0364 |

### dev1-ladder

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 6.81-7.8 | 103 | 0.0698 | 0.0410 | 0.214 |
| load (1-min) | 7.8-8.02 | 125 | 0.0836 | 0.0662 | 0.256 |
| load (1-min) | 8.02-8.14 | 114 | 0.0921 | 0.0713 | 0.246 |
| load (1-min) | 8.14-8.18 | 111 | 0.0777 | 0.0754 | 0.27 |
| load (1-min) | 8.18-8.24 | 123 | 0.0959 | 0.0707 | 0.244 |
| preference's time (s) | 0.0285-0.0444 | 115 | 0.0787 | 0.0648 | 0.183 |
| preference's time (s) | 0.0444-0.0484 | 115 | 0.0697 | 0.0512 | 0.148 |
| preference's time (s) | 0.0484-0.0531 | 115 | 0.0697 | 0.0460 | 0.191 |
| preference's time (s) | 0.0531-0.0597 | 115 | 0.0890 | 0.0793 | 0.313 |
| preference's time (s) | 0.0597-0.089 | 116 | 0.1012 | 0.0935 | 0.397 |
| timed runs in the round | 3.5-4.5 | 565 | 0.0835 | 0.0634 | 0.244 |
| timed runs in the round | 4.5-99 | 11 | 0.1358 | 0.1487 | 0.364 |
| round of the contest | 1-2 | 64 | 0.0901 | 0.0616 | 0.328 |
| round of the contest | 2-4 | 128 | 0.0539 | 0.0441 | 0.164 |
| round of the contest | 4-6 | 16 | 0.0725 | 0.0618 | 0.25 |
| round of the contest | 6-11 | 40 | 0.0940 | 0.0519 | 0.175 |
| round of the contest | 11-21 | 80 | 0.0862 | 0.0719 | 0.25 |
| round of the contest | 21-1e+03 | 248 | 0.0936 | 0.0781 | 0.278 |

### dev1-replay-solo

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 1.2-1.4 | 53 | 0.0192 | 0.0106 | 0 |
| load (1-min) | 1.4-1.77 | 60 | 0.0163 | 0.0085 | 0 |
| load (1-min) | 1.77-2.18 | 53 | 0.0064 | 0.0048 | 0 |
| load (1-min) | 2.18-3.55 | 54 | 0.0480 | 0.0087 | 0 |
| load (1-min) | 3.55-7.22 | 63 | 0.0111 | 0.0078 | 0 |
| preference's time (s) | 0.00101-0.00237 | 57 | 0.0184 | 0.0074 | 0 |
| preference's time (s) | 0.00237-0.00486 | 56 | 0.0111 | 0.0082 | 0 |
| preference's time (s) | 0.00486-0.00858 | 57 | 0.0480 | 0.0077 | 0 |
| preference's time (s) | 0.00858-0.0147 | 56 | 0.0103 | 0.0086 | 0 |
| preference's time (s) | 0.0147-0.0328 | 57 | 0.0083 | 0.0070 | 0 |
| timed runs in the round | 2.5-3.5 | 40 | 0.0167 | 0.0064 | 0 |
| timed runs in the round | 3.5-4.5 | 243 | 0.0254 | 0.0081 | 0 |
| round of the contest | 1-2 | 89 | 0.0389 | 0.0076 | 0 |
| round of the contest | 2-4 | 178 | 0.0133 | 0.0075 | 0 |
| round of the contest | 4-6 | 16 | 0.0075 | 0.0054 | 0 |

## The current rule's false-switch rate (TIE 5%, 75% share, minimum 5, cap 10)

The first contest draws rounds 1-3 from their own samples and later rounds by parity; the confirmation, a contest that starts later, draws every round from the later rounds (contest rounds after the third, and confirmation rounds), by parity. The last but one column draws the confirmation from the logged confirmation rounds alone (pooled; with the range its 95% interval gives), where at least 20 were logged.

| group | P(round win) [95% CI] | rounds 1 / 2 / 3, later odd / even | contest, m=1 | confirmed, m=1 | confirmed, m | m | confirmed, m, every sample at its 95% CI's upper end | with the contest effect (tau) | confirmed, m, from the logged confirmations [95% CI] (rounds) | rounds (equal arms) |
|---|---|---|---|---|---|---|---|---|---|---|
| dev2-replay | 0.273 [0.259, 0.287] | 0.396 / 0.228 / 0.317 / 0.279 / 0.217 | 0.026 | 0.00046 | 0.00091 | 2 | 0.002 | 0.044 (0.040) | 0.00048 [0.00012, 0.0016] (140) | 4.16 |
| dev2-ladder | 0.261 [0.212, 0.316] | 0.406 / 0.406 / 0.344 / 0.208 / 0.192 | 0.032 | 0.00024 | 0.00047 | 2 | 0.0082 | 0.018 (0.032) | - | 4.36 |
| dev2-replay-solo | 0.356 [0.305, 0.41] | 0.449 / 0.303 / 0.449 / 0.171 / 0.188 | 0.03 | 0.00014 | 0.00027 | 2 | 0.015 | 0.057 (0.051) | 0.00014 [3e-06, 0.002] (40) | 4.39 |
| dev2-ladder-lowload | 0.19 [0.134, 0.256] | 0.308 / 0.077 / 0.308 / 0.146 / 0.167 | 0.0052 | 1.3e-05 | 2.7e-05 | 2 | 0.0037 | 0.00034 (0.014) | - | 3.81 |
| dev2-replay-solo-lowload | 0.232 [0.186, 0.282] | 0.511 / 0.114 / 0.159 / 0.107 / 0.043 | 0.002 | 3.2e-07 | 6.4e-07 | 2 | 0.0011 | 6.4e-07 (0.000) | 1e-06 [2e-09, 4.9e-05] (35) | 3.83 |
| dev1-replay | 0.0368 [0.0309, 0.0435] | 0.079 / 0.027 / 0.052 / 0.024 / 0.029 | 1.1e-05 | 2.3e-11 | 4.7e-11 | 2 | 9e-10 | 1.8e-08 (0.007) | <1e-12 [<1e-12, 5.5e-10] (75) | 3.16 |
| dev1-ladder | 0.247 [0.212, 0.284] | 0.328 / 0.172 / 0.156 / 0.260 / 0.260 | 0.013 | 0.00025 | 0.0005 | 2 | 0.0047 | 0.0005 (0.000) | - | 3.85 |
| dev1-replay-solo | 0 [0, 0.013] | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | <1e-12 | <1e-12 | <1e-12 | 2 | 2.2e-07 | <1e-12 (0.000) | <1e-12 [<1e-12, <1e-12] (20) | 3.00 |

On the logged A/A sequences in their order (contests of at least 10 or 20 rounds, cut into windows from round 1, so a contest's first window holds its first rounds), against the switches the model expects at each window's place:

| group | window | rule | windows | switches | expected (model) |
|---|---|---|---|---|---|
| dev2-replay | 10 | current rule, one contest (no confirmation) | 232 | 4 | 5.01 |
| dev2-replay | 10 | sign test, delta 0, alpha 0.01 | 232 | 4 | 2.35 |
| dev2-replay | 10 | sign test, delta 0, alpha 0.001 | 232 | 0 | 0.28 |
| dev2-replay | 10 | sign test, delta 0.02, alpha 0.01 | 232 | 1 | 0.406 |
| dev2-replay | 10 | sign test, delta 0.02, alpha 0.001 | 232 | 0 | 0.0219 |
| dev2-replay | 20 | current rule, one contest (no confirmation) | 110 | 4 | 2.88 |
| dev2-replay | 20 | sign test, delta 0, alpha 0.01 | 110 | 1 | 1.32 |
| dev2-replay | 20 | sign test, delta 0, alpha 0.001 | 110 | 0 | 0.101 |
| dev2-replay | 20 | sign test, delta 0.02, alpha 0.01 | 110 | 0 | 0.124 |
| dev2-replay | 20 | sign test, delta 0.02, alpha 0.001 | 110 | 0 | 0.00331 |
| dev2-ladder | 10 | current rule, one contest (no confirmation) | 20 | 0 | 0.247 |
| dev2-ladder | 10 | sign test, delta 0, alpha 0.01 | 20 | 0 | 0.172 |
| dev2-ladder | 10 | sign test, delta 0, alpha 0.001 | 20 | 0 | 0.0215 |
| dev2-ladder | 10 | sign test, delta 0.02, alpha 0.01 | 20 | 0 | 0.0109 |
| dev2-ladder | 10 | sign test, delta 0.02, alpha 0.001 | 20 | 0 | 3.3e-04 |
| dev2-ladder | 20 | current rule, one contest (no confirmation) | 8 | 0 | 0.159 |
| dev2-ladder | 20 | sign test, delta 0, alpha 0.01 | 8 | 0 | 0.0847 |
| dev2-ladder | 20 | sign test, delta 0, alpha 0.001 | 8 | 0 | 0.00612 |
| dev2-ladder | 20 | sign test, delta 0.02, alpha 0.01 | 8 | 0 | 0.00207 |
| dev2-ladder | 20 | sign test, delta 0.02, alpha 0.001 | 8 | 0 | 2.6e-05 |
| dev2-ladder-lowload | 10 | current rule, one contest (no confirmation) | 10 | 1 | 0.031 |
| dev2-ladder-lowload | 10 | sign test, delta 0, alpha 0.01 | 10 | 0 | 0.0491 |
| dev2-ladder-lowload | 10 | sign test, delta 0, alpha 0.001 | 10 | 0 | 0.00493 |
| dev2-ladder-lowload | 10 | sign test, delta 0.02, alpha 0.01 | 10 | 0 | 0.00208 |
| dev2-ladder-lowload | 10 | sign test, delta 0.02, alpha 0.001 | 10 | 0 | 5.2e-05 |
| dev2-ladder-lowload | 20 | current rule, one contest (no confirmation) | 4 | 0 | 0.0156 |
| dev2-ladder-lowload | 20 | sign test, delta 0, alpha 0.01 | 4 | 0 | 0.0227 |
| dev2-ladder-lowload | 20 | sign test, delta 0, alpha 0.001 | 4 | 0 | 0.00114 |
| dev2-ladder-lowload | 20 | sign test, delta 0.02, alpha 0.01 | 4 | 0 | 3.6e-04 |
| dev2-ladder-lowload | 20 | sign test, delta 0.02, alpha 0.001 | 4 | 0 | 2.8e-06 |
| dev1-replay | 10 | current rule, one contest (no confirmation) | 225 | 0 | 0.00142 |
| dev1-replay | 10 | sign test, delta 0, alpha 0.01 | 225 | 5 | 1.94 |
| dev1-replay | 10 | sign test, delta 0, alpha 0.001 | 225 | 1 | 0.268 |
| dev1-replay | 10 | sign test, delta 0.02, alpha 0.01 | 225 | 0 | 0.00373 |
| dev1-replay | 10 | sign test, delta 0.02, alpha 0.001 | 225 | 0 | 3.1e-05 |
| dev1-replay | 20 | current rule, one contest (no confirmation) | 108 | 0 | 0.00116 |
| dev1-replay | 20 | sign test, delta 0, alpha 0.01 | 108 | 0 | 1.28 |
| dev1-replay | 20 | sign test, delta 0, alpha 0.001 | 108 | 0 | 0.093 |
| dev1-replay | 20 | sign test, delta 0.02, alpha 0.01 | 108 | 0 | 5.3e-04 |
| dev1-replay | 20 | sign test, delta 0.02, alpha 0.001 | 108 | 0 | 8.5e-07 |
| dev1-ladder | 10 | current rule, one contest (no confirmation) | 40 | 0 | 0.738 |
| dev1-ladder | 10 | sign test, delta 0, alpha 0.01 | 40 | 0 | 0.394 |
| dev1-ladder | 10 | sign test, delta 0, alpha 0.001 | 40 | 0 | 0.0545 |
| dev1-ladder | 10 | sign test, delta 0.02, alpha 0.01 | 40 | 0 | 0.0316 |
| dev1-ladder | 10 | sign test, delta 0.02, alpha 0.001 | 40 | 0 | 0.00151 |
| dev1-ladder | 20 | current rule, one contest (no confirmation) | 16 | 0 | 0.262 |
| dev1-ladder | 20 | sign test, delta 0, alpha 0.01 | 16 | 0 | 0.218 |
| dev1-ladder | 20 | sign test, delta 0, alpha 0.001 | 16 | 0 | 0.017 |
| dev1-ladder | 20 | sign test, delta 0.02, alpha 0.01 | 16 | 0 | 0.0066 |
| dev1-ladder | 20 | sign test, delta 0.02, alpha 0.001 | 16 | 0 | 1.3e-04 |

## Rules under the dev2-replay null (3911 rounds; m = 2)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.00046 | 0.00091 | 0.003 | 0.068 | 0.641 | 4.2 | 5.5 |
| 20 | 0.00046 | 0.00092 | 0.003 | 0.076 | 0.794 | 6.8 | 7.2 |
| 30 | 0.00046 | 0.00092 | 0.003 | 0.077 | 0.834 | 7.6 | 8.0 |
| 40 | 0.00046 | 0.00092 | 0.003 | 0.077 | 0.870 | 8.6 | 8.8 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.011 | 0.0098 | 0.029 | 0.122 | 0.330 | 2.2 | 3.8 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.012 | 0.013 | 0.067 | 0.360 | 0.797 | 8.3 | 13.4 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.014 | 0.014 | 0.110 | 0.580 | 0.955 | 16.4 | 20.4 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.014 | 0.014 | 0.160 | 0.762 | 0.994 | 22.4 | 26.4 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0013 | no test at alpha/m | - | - | - | 2.2 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.00092 | 0.0013 | 0.014 | 0.149 | 0.552 | 6.3 | 11.9 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.0014 | 0.0015 | 0.029 | 0.328 | 0.853 | 12.4 | 21.8 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0015 | 0.0015 | 0.041 | 0.477 | 0.955 | 18.5 | 29.8 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.00013 | 0.00014 | 0.003 | 0.045 | 0.280 | 4.3 | 8.4 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.00015 | 0.00015 | 0.005 | 0.110 | 0.558 | 10.4 | 16.4 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.00015 | 0.00015 | 0.009 | 0.235 | 0.829 | 16.5 | 27.4 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.002 | 0.0014 | 0.005 | 0.053 | 0.257 | 1.9 | 3.1 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0011 | 0.00095 | 0.006 | 0.142 | 0.681 | 6.8 | 11.9 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.00074 | 0.00059 | 0.007 | 0.246 | 0.893 | 13.4 | 19.9 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0006 | 0.00045 | 0.007 | 0.361 | 0.975 | 18.3 | 29.3 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.00011 | no test at alpha/m | - | - | - | 1.9 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 3e-05 | 4.4e-05 | 0.001 | 0.040 | 0.413 | 5.2 | 9.6 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 3.4e-05 | 2.7e-05 | 0.001 | 0.089 | 0.725 | 10.1 | 18.8 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 3e-05 | 2.5e-05 | 0.001 | 0.134 | 0.878 | 15.0 | 27.6 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 3e-06 | 2.6e-06 | 0.000 | 0.009 | 0.180 | 3.5 | 6.5 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.7e-06 | 1.5e-06 | 0.000 | 0.019 | 0.394 | 8.5 | 13.0 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 9.1e-07 | 7.6e-07 | 0.000 | 0.041 | 0.672 | 13.4 | 22.5 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00011 | 4.6e-05 | 0.000 | 0.005 | 0.131 | 1.5 | 2.2 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 2.6e-05 | 1.4e-05 | 0.000 | 0.006 | 0.384 | 5.6 | 8.3 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 8.8e-06 | 4.3e-06 | 0.000 | 0.007 | 0.610 | 10.9 | 14.4 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 7.2e-06 | 3.2e-06 | 0.000 | 0.007 | 0.789 | 14.9 | 22.5 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 1.4e-06 | no test at alpha/m | - | - | - | 1.5 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 9.9e-08 | 1.8e-07 | 0.000 | 0.001 | 0.164 | 4.2 | 6.3 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 1e-07 | 5.4e-08 | 0.000 | 0.001 | 0.356 | 8.2 | 12.4 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 9.6e-08 | 5.4e-08 | 0.000 | 0.001 | 0.513 | 12.2 | 18.6 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 5.3e-09 | 2.9e-09 | 0.000 | 0.000 | 0.051 | 2.9 | 4.3 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.5e-09 | 7.3e-10 | 0.000 | 0.000 | 0.124 | 6.9 | 8.3 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 3.7e-10 | 2.1e-10 | 0.000 | 0.000 | 0.262 | 10.9 | 14.5 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00147 | 0.0097 | 0.025 | 0.139 | 0.469 | 10.0 |
| t | 0 | 0.01 | 20 | 7.9e-04 | 0.01 | 0.039 | 0.236 | 0.694 | 19.9 |
| t | 0 | 0.01 | 30 | 6.4e-04 | 0.01 | 0.047 | 0.309 | 0.827 | 29.9 |
| t | 0 | 0.01 | 40 | 4.8e-04 | 0.01 | 0.052 | 0.358 | 0.893 | 39.9 |
| t | 0 | 0.001 | 10 | 1.1e-04 | 0.00088 | 0.004 | 0.039 | 0.247 | 10.0 |
| t | 0 | 0.001 | 20 | 6.0e-05 | 0.0012 | 0.007 | 0.092 | 0.493 | 20.0 |
| t | 0 | 0.001 | 30 | 5.0e-05 | 0.001 | 0.008 | 0.118 | 0.623 | 30.0 |
| t | 0 | 0.001 | 40 | 5.0e-05 | 0.0012 | 0.013 | 0.196 | 0.795 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00141 | 0.0018 | 0.005 | 0.053 | 0.358 | 10.0 |
| t | 0.02 | 0.01 | 20 | 8.4e-04 | 0.0014 | 0.005 | 0.084 | 0.544 | 20.0 |
| t | 0.02 | 0.01 | 30 | 6.0e-04 | 0.0011 | 0.005 | 0.104 | 0.667 | 30.0 |
| t | 0.02 | 0.01 | 40 | 5.2e-04 | 0.00072 | 0.005 | 0.124 | 0.776 | 40.0 |
| t | 0.02 | 0.001 | 10 | 1.3e-04 | 8e-05 | 0.000 | 0.009 | 0.141 | 10.0 |
| t | 0.02 | 0.001 | 20 | 4.0e-05 | 2e-05 | 0.001 | 0.021 | 0.340 | 20.0 |
| t | 0.02 | 0.001 | 30 | 4.0e-05 | 0.00014 | 0.000 | 0.027 | 0.452 | 30.0 |
| t | 0.02 | 0.001 | 40 | 3.0e-05 | 0.00018 | 0.001 | 0.047 | 0.615 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00278 | 0.0077 | 0.026 | 0.130 | 0.381 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00142 | 0.0091 | 0.049 | 0.266 | 0.658 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 9.8e-04 | 0.01 | 0.065 | 0.403 | 0.847 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 8.1e-04 | 0.01 | 0.085 | 0.542 | 0.945 | 39.9 |
| wilcoxon | 0 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 1.6e-04 | 0.001 | 0.009 | 0.095 | 0.371 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 8.0e-05 | 0.00092 | 0.013 | 0.172 | 0.608 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 9.0e-05 | 0.0013 | 0.023 | 0.303 | 0.831 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00281 | 0.00074 | 0.004 | 0.053 | 0.293 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00134 | 0.00048 | 0.005 | 0.106 | 0.543 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00102 | 0.00032 | 0.005 | 0.158 | 0.739 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 7.9e-04 | 0.00026 | 0.005 | 0.215 | 0.867 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 1.7e-04 | <1e-12 | 0.001 | 0.029 | 0.276 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 1.1e-04 | 4e-05 | 0.001 | 0.053 | 0.487 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 5.0e-05 | 2e-05 | 0.001 | 0.075 | 0.668 | 40.0 |

## Rules under the dev2-ladder null (291 rounds; m = 2)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.00024 | 0.00047 | 0.001 | 0.061 | 0.723 | 4.4 | 5.6 |
| 20 | 0.00024 | 0.00047 | 0.001 | 0.069 | 0.894 | 6.9 | 7.3 |
| 30 | 0.00024 | 0.00047 | 0.001 | 0.069 | 0.930 | 7.7 | 7.8 |
| 40 | 0.00024 | 0.00047 | 0.001 | 0.069 | 0.956 | 8.6 | 8.2 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.01 | 0.01 | 0.019 | 0.136 | 0.327 | 2.1 | 3.4 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.011 | 0.012 | 0.042 | 0.493 | 0.861 | 8.2 | 13.8 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.012 | 0.012 | 0.068 | 0.764 | 0.982 | 16.2 | 19.8 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.012 | 0.012 | 0.096 | 0.918 | 0.999 | 22.2 | 23.5 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0013 | no test at alpha/m | - | - | - | 2.1 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.00083 | 0.0012 | 0.008 | 0.246 | 0.650 | 6.3 | 12.6 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.0012 | 0.0013 | 0.015 | 0.534 | 0.929 | 12.3 | 22.6 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0013 | 0.0013 | 0.021 | 0.729 | 0.988 | 18.3 | 28.9 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.00012 | 0.00012 | 0.001 | 0.087 | 0.364 | 4.2 | 8.8 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.00012 | 0.00013 | 0.002 | 0.226 | 0.695 | 10.3 | 18.1 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.00012 | 0.00012 | 0.004 | 0.465 | 0.928 | 16.3 | 29.1 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00094 | 0.00053 | 0.005 | 0.060 | 0.278 | 1.7 | 3.0 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00035 | 0.00026 | 0.006 | 0.183 | 0.812 | 6.4 | 12.3 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.00017 | 0.00011 | 0.006 | 0.327 | 0.969 | 12.4 | 20.4 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.00014 | 8.2e-05 | 0.006 | 0.480 | 0.997 | 16.8 | 29.2 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 2.8e-05 | no test at alpha/m | - | - | - | 1.7 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 4.3e-06 | 6.9e-06 | 0.001 | 0.058 | 0.576 | 4.9 | 9.9 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 4.5e-06 | 3.2e-06 | 0.001 | 0.136 | 0.891 | 9.4 | 19.7 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 4.1e-06 | 3.1e-06 | 0.001 | 0.211 | 0.976 | 13.9 | 28.7 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 3.5e-07 | 2.6e-07 | 0.000 | 0.014 | 0.298 | 3.4 | 6.6 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.4e-07 | 9.9e-08 | 0.000 | 0.033 | 0.615 | 7.9 | 13.7 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 5.3e-08 | 3.9e-08 | 0.000 | 0.075 | 0.885 | 12.4 | 23.9 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 9.1e-05 | 3.5e-05 | 0.000 | 0.005 | 0.143 | 1.6 | 2.1 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 1.8e-05 | 7.7e-06 | 0.000 | 0.006 | 0.529 | 5.7 | 8.2 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 4.5e-06 | 1.8e-06 | 0.000 | 0.006 | 0.801 | 10.7 | 14.2 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 3.8e-06 | 1.5e-06 | 0.000 | 0.006 | 0.940 | 14.4 | 22.3 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 7e-07 | no test at alpha/m | - | - | - | 1.6 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 3e-08 | 5.7e-08 | 0.000 | 0.001 | 0.275 | 4.4 | 6.3 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 3e-08 | 1.2e-08 | 0.000 | 0.001 | 0.584 | 8.2 | 12.3 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 3e-08 | 1.2e-08 | 0.000 | 0.001 | 0.778 | 11.9 | 18.3 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 1.1e-09 | 4.7e-10 | 0.000 | 0.000 | 0.101 | 3.1 | 4.2 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 2.4e-10 | 9.8e-11 | 0.000 | 0.000 | 0.261 | 6.9 | 8.3 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 4.9e-11 | 2.1e-11 | 0.000 | 0.000 | 0.524 | 10.7 | 14.3 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00162 | 0.01 | 0.029 | 0.161 | 0.501 | 10.0 |
| t | 0 | 0.01 | 20 | 8.3e-04 | 0.01 | 0.046 | 0.311 | 0.771 | 20.0 |
| t | 0 | 0.01 | 30 | 7.0e-04 | 0.01 | 0.060 | 0.443 | 0.861 | 29.9 |
| t | 0 | 0.01 | 40 | 5.4e-04 | 0.0096 | 0.078 | 0.550 | 0.923 | 39.9 |
| t | 0 | 0.001 | 10 | 1.4e-04 | 0.0011 | 0.005 | 0.056 | 0.300 | 10.0 |
| t | 0 | 0.001 | 20 | 6.0e-05 | 0.0015 | 0.010 | 0.148 | 0.637 | 20.0 |
| t | 0 | 0.001 | 30 | 4.0e-05 | 0.0011 | 0.015 | 0.269 | 0.798 | 30.0 |
| t | 0 | 0.001 | 40 | 4.0e-05 | 0.0011 | 0.021 | 0.370 | 0.867 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00148 | 0.0017 | 0.005 | 0.061 | 0.376 | 10.0 |
| t | 0.02 | 0.01 | 20 | 8.4e-04 | 0.0012 | 0.005 | 0.109 | 0.658 | 20.0 |
| t | 0.02 | 0.01 | 30 | 6.6e-04 | 0.0012 | 0.005 | 0.153 | 0.775 | 30.0 |
| t | 0.02 | 0.01 | 40 | 5.4e-04 | 0.00084 | 0.004 | 0.199 | 0.844 | 40.0 |
| t | 0.02 | 0.001 | 10 | 1.1e-04 | 4e-05 | 0.001 | 0.014 | 0.196 | 10.0 |
| t | 0.02 | 0.001 | 20 | 7.0e-05 | 0.0002 | 0.001 | 0.033 | 0.468 | 20.0 |
| t | 0.02 | 0.001 | 30 | 5.0e-05 | 8e-05 | 0.001 | 0.067 | 0.691 | 30.0 |
| t | 0.02 | 0.001 | 40 | 3.0e-05 | 0.00012 | 0.001 | 0.096 | 0.779 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00384 | 0.0098 | 0.032 | 0.194 | 0.466 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.0014 | 0.0099 | 0.061 | 0.414 | 0.823 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 0.0011 | 0.0097 | 0.109 | 0.662 | 0.973 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 7.8e-04 | 0.0094 | 0.146 | 0.819 | 0.997 | 39.9 |
| wilcoxon | 0 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 1.6e-04 | 0.0011 | 0.015 | 0.208 | 0.585 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 9.0e-05 | 0.0011 | 0.026 | 0.398 | 0.884 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 8.0e-05 | 0.0012 | 0.048 | 0.599 | 0.977 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00407 | 0.00064 | 0.005 | 0.080 | 0.376 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00154 | 0.00026 | 0.005 | 0.171 | 0.716 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00114 | 0.0002 | 0.004 | 0.295 | 0.925 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 8.6e-04 | 0.00014 | 0.005 | 0.411 | 0.982 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 1.5e-04 | <1e-12 | 0.000 | 0.051 | 0.419 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 1.1e-04 | <1e-12 | 0.001 | 0.118 | 0.777 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 8.0e-05 | <1e-12 | 0.000 | 0.172 | 0.890 | 40.0 |

## Rules under the dev2-replay-solo null (334 rounds; m = 2)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.00014 | 0.00027 | 0.001 | 0.023 | 0.570 | 4.4 | 5.5 |
| 20 | 0.00014 | 0.00027 | 0.001 | 0.024 | 0.701 | 6.9 | 7.4 |
| 30 | 0.00014 | 0.00027 | 0.001 | 0.024 | 0.737 | 7.6 | 8.4 |
| 40 | 0.00014 | 0.00027 | 0.001 | 0.024 | 0.770 | 8.4 | 9.7 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0044 | 0.0025 | 0.018 | 0.081 | 0.403 | 2.3 | 3.8 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0019 | 0.0018 | 0.030 | 0.226 | 0.920 | 7.5 | 12.9 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0013 | 0.00099 | 0.039 | 0.379 | 0.994 | 14.2 | 20.6 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0011 | 0.00071 | 0.048 | 0.538 | 1.000 | 19.2 | 28.8 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.00018 | no test at alpha/m | - | - | - | 2.3 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 4.8e-05 | 6.9e-05 | 0.004 | 0.073 | 0.754 | 5.9 | 10.9 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 5.4e-05 | 4.7e-05 | 0.007 | 0.165 | 0.969 | 10.9 | 20.5 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 4.6e-05 | 4.4e-05 | 0.008 | 0.249 | 0.997 | 15.9 | 29.3 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 4.6e-06 | 4.4e-06 | 0.001 | 0.018 | 0.472 | 4.2 | 7.6 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 2.8e-06 | 2e-06 | 0.001 | 0.040 | 0.803 | 9.2 | 14.7 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 1.2e-06 | 1.2e-06 | 0.001 | 0.090 | 0.971 | 14.2 | 25.0 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0012 | 0.00058 | 0.001 | 0.038 | 0.368 | 2.0 | 3.2 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00036 | 0.00026 | 0.001 | 0.087 | 0.909 | 6.7 | 11.3 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.00016 | 0.0001 | 0.000 | 0.139 | 0.993 | 12.5 | 19.1 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.00014 | 7.2e-05 | 0.000 | 0.199 | 1.000 | 16.8 | 28.9 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 2.7e-05 | no test at alpha/m | - | - | - | 2.0 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 3.4e-06 | 5.6e-06 | 0.000 | 0.019 | 0.731 | 5.2 | 9.0 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 3.5e-06 | 2.4e-06 | 0.000 | 0.039 | 0.965 | 9.6 | 17.4 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 3.2e-06 | 2.4e-06 | 0.000 | 0.055 | 0.996 | 13.9 | 25.7 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 2.5e-07 | 1.8e-07 | 0.000 | 0.004 | 0.445 | 3.7 | 6.2 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 9.9e-08 | 5.9e-08 | 0.000 | 0.007 | 0.785 | 8.1 | 12.0 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 3.1e-08 | 2.3e-08 | 0.000 | 0.013 | 0.967 | 12.5 | 20.5 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 6.3e-05 | 2.4e-05 | 0.000 | 0.001 | 0.095 | 1.7 | 2.3 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 1.2e-05 | 4.2e-06 | 0.000 | 0.001 | 0.270 | 5.7 | 7.5 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 2.4e-06 | 9.2e-07 | 0.000 | 0.000 | 0.448 | 10.6 | 12.5 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 2.1e-06 | 8e-07 | 0.000 | 0.000 | 0.621 | 14.2 | 19.2 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 3.8e-07 | no test at alpha/m | - | - | - | 1.7 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 1.3e-08 | 2.5e-08 | 0.000 | 0.000 | 0.095 | 4.5 | 5.9 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 1.3e-08 | 4.4e-09 | 0.000 | 0.000 | 0.214 | 8.1 | 10.9 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 1.3e-08 | 4.4e-09 | 0.000 | 0.000 | 0.320 | 11.8 | 15.9 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 4e-10 | 1.4e-10 | 0.000 | 0.000 | 0.025 | 3.1 | 4.2 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 6.9e-11 | 2.7e-11 | 0.000 | 0.000 | 0.058 | 6.9 | 7.5 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 1.4e-11 | 4.7e-12 | 0.000 | 0.000 | 0.130 | 10.6 | 12.5 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00145 | 0.0085 | 0.025 | 0.187 | 0.692 | 10.0 |
| t | 0 | 0.01 | 20 | 8.2e-04 | 0.0098 | 0.051 | 0.469 | 0.969 | 20.0 |
| t | 0 | 0.01 | 30 | 6.4e-04 | 0.011 | 0.081 | 0.700 | 0.992 | 29.9 |
| t | 0 | 0.01 | 40 | 4.9e-04 | 0.01 | 0.099 | 0.835 | 0.999 | 39.9 |
| t | 0 | 0.001 | 10 | 1.2e-04 | 0.0012 | 0.004 | 0.052 | 0.427 | 10.0 |
| t | 0 | 0.001 | 20 | 6.0e-05 | 0.00098 | 0.010 | 0.229 | 0.893 | 20.0 |
| t | 0 | 0.001 | 30 | 4.0e-05 | 0.0012 | 0.022 | 0.490 | 0.986 | 30.0 |
| t | 0 | 0.001 | 40 | 5.0e-05 | 0.0011 | 0.035 | 0.697 | 0.998 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00144 | 0.0022 | 0.005 | 0.062 | 0.539 | 10.0 |
| t | 0.02 | 0.01 | 20 | 8.7e-04 | 0.0015 | 0.005 | 0.144 | 0.901 | 20.0 |
| t | 0.02 | 0.01 | 30 | 6.0e-04 | 0.0008 | 0.004 | 0.223 | 0.979 | 30.0 |
| t | 0.02 | 0.01 | 40 | 5.4e-04 | 0.00098 | 0.005 | 0.321 | 0.993 | 40.0 |
| t | 0.02 | 0.001 | 10 | 1.1e-04 | 0.00022 | 0.000 | 0.011 | 0.279 | 10.0 |
| t | 0.02 | 0.001 | 20 | 6.0e-05 | 0.00018 | 0.001 | 0.043 | 0.752 | 20.0 |
| t | 0.02 | 0.001 | 30 | 4.0e-05 | 4e-05 | 0.000 | 0.080 | 0.947 | 30.0 |
| t | 0.02 | 0.001 | 40 | 3.0e-05 | 0.0001 | 0.001 | 0.149 | 0.987 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00295 | 0.01 | 0.044 | 0.255 | 0.743 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00131 | 0.01 | 0.091 | 0.621 | 0.995 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 8.9e-04 | 0.0098 | 0.135 | 0.862 | 1.000 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 7.3e-04 | 0.0088 | 0.182 | 0.959 | 1.000 | 39.9 |
| wilcoxon | 0 | 0.001 | 10 | 3.6e-04 | 0.00052 | 0.009 | 0.087 | 0.457 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 1.4e-04 | 0.00086 | 0.019 | 0.318 | 0.955 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 7.0e-05 | 0.001 | 0.037 | 0.647 | 1.000 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 7.0e-05 | 0.00088 | 0.061 | 0.858 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00301 | 0.001 | 0.005 | 0.094 | 0.579 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00127 | 0.00052 | 0.005 | 0.212 | 0.958 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 9.1e-04 | 0.0007 | 0.006 | 0.366 | 0.999 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 7.6e-04 | 0.00022 | 0.005 | 0.510 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 4.4e-04 | 8e-05 | 0.000 | 0.023 | 0.350 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 1.4e-04 | 2e-05 | 0.000 | 0.075 | 0.860 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 8.0e-05 | <1e-12 | 0.000 | 0.155 | 0.989 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 6.0e-05 | 8e-05 | 0.001 | 0.282 | 1.000 | 40.0 |

## Rules under the dev2-ladder-lowload null (174 rounds; m = 2)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 1.3e-05 | 2.7e-05 | 0.000 | 0.043 | 0.961 | 3.8 | 5.1 |
| 20 | 1.3e-05 | 2.7e-05 | 0.000 | 0.047 | 0.995 | 6.0 | 5.1 |
| 30 | 1.3e-05 | 2.7e-05 | 0.000 | 0.047 | 0.998 | 6.3 | 5.1 |
| 40 | 1.3e-05 | 2.7e-05 | 0.000 | 0.047 | 0.999 | 6.6 | 5.1 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0084 | 0.008 | 0.060 | 0.499 | 0.959 | 2.3 | 6.5 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0074 | 0.0067 | 0.122 | 0.892 | 1.000 | 8.1 | 12.5 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0061 | 0.0056 | 0.183 | 0.982 | 1.000 | 15.4 | 14.4 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0053 | 0.005 | 0.249 | 0.998 | 1.000 | 21.0 | 15.0 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.00085 | no test at alpha/m | - | - | - | 2.3 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.00038 | 0.00055 | 0.030 | 0.690 | 1.000 | 6.3 | 15.2 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.00048 | 0.00043 | 0.056 | 0.922 | 1.000 | 11.8 | 19.7 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.00045 | 0.0004 | 0.076 | 0.981 | 1.000 | 17.4 | 20.9 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 4.8e-05 | 4.4e-05 | 0.006 | 0.399 | 0.989 | 4.4 | 14.3 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 3.6e-05 | 3.8e-05 | 0.011 | 0.689 | 1.000 | 10.0 | 21.1 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 2.9e-05 | 2.5e-05 | 0.020 | 0.905 | 1.000 | 15.5 | 26.2 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00032 | 0.00019 | 0.004 | 0.123 | 0.849 | 1.7 | 4.4 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00011 | 6.7e-05 | 0.003 | 0.287 | 1.000 | 6.0 | 13.2 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 4.5e-05 | 2.7e-05 | 0.003 | 0.445 | 1.000 | 11.7 | 20.4 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 3.5e-05 | 2.1e-05 | 0.003 | 0.596 | 1.000 | 15.9 | 27.8 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 8e-06 | no test at alpha/m | - | - | - | 1.7 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 8.9e-07 | 1.5e-06 | 0.000 | 0.102 | 0.994 | 4.6 | 11.6 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 9.1e-07 | 5.1e-07 | 0.000 | 0.208 | 1.000 | 8.9 | 21.0 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 8.5e-07 | 5e-07 | 0.000 | 0.299 | 1.000 | 13.1 | 29.4 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 6.2e-08 | 3.6e-08 | 0.000 | 0.027 | 0.940 | 3.1 | 8.5 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.9e-08 | 1.3e-08 | 0.000 | 0.059 | 0.998 | 7.5 | 15.6 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 6.8e-09 | 4e-09 | 0.000 | 0.120 | 1.000 | 11.7 | 25.7 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 4.3e-06 | 1.4e-06 | 0.000 | 0.004 | 0.556 | 1.3 | 2.3 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 7.4e-07 | 2.2e-07 | 0.000 | 0.003 | 0.924 | 5.0 | 8.1 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 1.3e-07 | 4.2e-08 | 0.000 | 0.003 | 0.990 | 9.8 | 13.6 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 1.1e-07 | 3.6e-08 | 0.000 | 0.003 | 0.999 | 13.3 | 21.0 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 1.7e-08 | no test at alpha/m | - | - | - | 1.3 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 4.4e-10 | 8.5e-10 | 0.000 | 0.000 | 0.752 | 3.8 | 6.3 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 4.4e-10 | 1.3e-10 | 0.000 | 0.000 | 0.950 | 7.4 | 11.8 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 4.4e-10 | 1.3e-10 | 0.000 | 0.000 | 0.990 | 10.9 | 17.4 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 1e-11 | 3e-12 | 0.000 | 0.000 | 0.464 | 2.5 | 4.4 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.5e-12 | <1e-12 | 0.000 | 0.000 | 0.758 | 6.2 | 8.1 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.940 | 9.8 | 13.7 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00138 | 0.01 | 0.064 | 0.570 | 0.998 | 10.0 |
| t | 0 | 0.01 | 20 | 7.6e-04 | 0.011 | 0.152 | 0.950 | 1.000 | 19.9 |
| t | 0 | 0.01 | 30 | 5.7e-04 | 0.01 | 0.248 | 0.997 | 1.000 | 29.9 |
| t | 0 | 0.01 | 40 | 5.1e-04 | 0.011 | 0.383 | 1.000 | 1.000 | 39.9 |
| t | 0 | 0.001 | 10 | 1.0e-04 | 0.00086 | 0.010 | 0.220 | 0.944 | 10.0 |
| t | 0 | 0.001 | 20 | 7.0e-05 | 0.0012 | 0.031 | 0.742 | 1.000 | 20.0 |
| t | 0 | 0.001 | 30 | 3.0e-05 | 0.0013 | 0.089 | 0.975 | 1.000 | 30.0 |
| t | 0 | 0.001 | 40 | 3.0e-05 | 0.00094 | 0.124 | 0.997 | 1.000 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00137 | 0.00056 | 0.005 | 0.184 | 0.974 | 10.0 |
| t | 0.02 | 0.01 | 20 | 7.4e-04 | 0.00024 | 0.005 | 0.459 | 1.000 | 20.0 |
| t | 0.02 | 0.01 | 30 | 5.8e-04 | 0.00028 | 0.004 | 0.701 | 1.000 | 30.0 |
| t | 0.02 | 0.01 | 40 | 4.8e-04 | 0.00044 | 0.005 | 0.850 | 1.000 | 40.0 |
| t | 0.02 | 0.001 | 10 | 1.1e-04 | 4e-05 | 0.000 | 0.027 | 0.699 | 10.0 |
| t | 0.02 | 0.001 | 20 | 6.0e-05 | 2e-05 | 0.001 | 0.187 | 1.000 | 20.0 |
| t | 0.02 | 0.001 | 30 | 4.0e-05 | 4e-05 | 0.001 | 0.405 | 1.000 | 30.0 |
| t | 0.02 | 0.001 | 40 | 4.0e-05 | <1e-12 | 0.000 | 0.629 | 1.000 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00342 | 0.0098 | 0.084 | 0.667 | 0.996 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00127 | 0.0078 | 0.189 | 0.972 | 1.000 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 8.9e-04 | 0.0099 | 0.319 | 0.999 | 1.000 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 7.2e-04 | 0.0097 | 0.428 | 1.000 | 1.000 | 39.9 |
| wilcoxon | 0 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 1.3e-04 | 0.001 | 0.063 | 0.877 | 1.000 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 1.0e-04 | 0.0008 | 0.115 | 0.987 | 1.000 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 7.0e-05 | 0.0015 | 0.199 | 0.999 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.0032 | 0.0002 | 0.004 | 0.201 | 0.962 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00128 | 8e-05 | 0.005 | 0.532 | 1.000 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 9.4e-04 | 4e-05 | 0.005 | 0.772 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 7.0e-04 | 2e-05 | 0.005 | 0.893 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 1.3e-04 | <1e-12 | 0.001 | 0.246 | 1.000 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 9.0e-05 | <1e-12 | 0.000 | 0.485 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 5.0e-05 | <1e-12 | 0.001 | 0.666 | 1.000 | 40.0 |

## Rules under the dev2-replay-solo-lowload null (315 rounds; m = 2)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 3.2e-07 | 6.4e-07 | 0.000 | 0.074 | 0.986 | 3.8 | 5.1 |
| 20 | 3.2e-07 | 6.4e-07 | 0.000 | 0.077 | 1.000 | 5.7 | 5.2 |
| 30 | 3.2e-07 | 6.4e-07 | 0.000 | 0.077 | 1.000 | 5.8 | 5.2 |
| 40 | 3.2e-07 | 6.4e-07 | 0.000 | 0.077 | 1.000 | 6.0 | 5.2 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0082 | 0.0036 | 0.373 | 0.486 | 0.829 | 2.6 | 5.7 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.004 | 0.0046 | 0.899 | 0.959 | 1.000 | 8.6 | 12.0 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0042 | 0.0034 | 0.991 | 0.998 | 1.000 | 16.6 | 13.2 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0042 | 0.0028 | 1.000 | 1.000 | 1.000 | 22.6 | 13.7 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0003 | no test at alpha/m | - | - | - | 2.6 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.00015 | 0.00018 | 0.714 | 0.843 | 1.000 | 6.6 | 15.2 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.00021 | 0.00021 | 0.957 | 0.988 | 1.000 | 12.7 | 17.6 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.00018 | 0.0002 | 0.994 | 0.999 | 1.000 | 18.7 | 17.9 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 1.4e-05 | 1.6e-05 | 0.427 | 0.590 | 0.990 | 4.6 | 14.8 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.4e-05 | 7.8e-06 | 0.761 | 0.889 | 1.000 | 10.6 | 20.6 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 7.8e-06 | 8e-06 | 0.957 | 0.990 | 1.000 | 16.7 | 22.9 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 2.3e-05 | 6e-06 | 0.002 | 0.404 | 0.780 | 1.9 | 5.4 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 3e-06 | 8.7e-07 | 0.002 | 0.910 | 1.000 | 5.8 | 12.7 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 4.7e-07 | 1.3e-07 | 0.002 | 0.992 | 1.000 | 10.4 | 14.3 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 4.4e-07 | 1.1e-07 | 0.001 | 1.000 | 1.000 | 13.9 | 15.0 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 5.6e-08 | no test at alpha/m | - | - | - | 1.9 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 1.1e-09 | 2.1e-09 | 0.000 | 0.734 | 1.000 | 4.6 | 15.3 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 1.1e-09 | 3e-10 | 0.000 | 0.961 | 1.000 | 8.1 | 19.1 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 1.1e-09 | 3e-10 | 0.000 | 0.995 | 1.000 | 11.6 | 19.8 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 1.9e-11 | 5.6e-12 | 0.000 | 0.450 | 0.982 | 3.3 | 13.9 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 2.8e-12 | <1e-12 | 0.000 | 0.777 | 1.000 | 6.9 | 21.2 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.961 | 1.000 | 10.4 | 24.9 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 2e-07 | 1.7e-08 | 0.000 | 0.002 | 0.537 | 1.6 | 2.6 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 8.7e-09 | 1.9e-09 | 0.000 | 0.002 | 0.982 | 4.9 | 8.6 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 9.5e-10 | 8.6e-11 | 0.000 | 0.002 | 1.000 | 9.2 | 14.6 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 9.4e-10 | 8.2e-11 | 0.000 | 0.001 | 1.000 | 12.5 | 22.7 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 4.1e-11 | no test at alpha/m | - | - | - | 1.6 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.911 | 3.8 | 6.6 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.997 | 7.1 | 12.7 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 10.3 | 18.7 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.702 | 2.7 | 4.6 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.951 | 6.0 | 8.6 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.998 | 9.2 | 14.7 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00161 | 0.012 | 0.326 | 0.788 | 0.981 | 10.0 |
| t | 0 | 0.01 | 20 | 9.5e-04 | 0.01 | 0.545 | 0.967 | 1.000 | 20.0 |
| t | 0 | 0.01 | 30 | 7.1e-04 | 0.0097 | 0.699 | 0.988 | 1.000 | 29.9 |
| t | 0 | 0.01 | 40 | 5.8e-04 | 0.0096 | 0.815 | 0.996 | 1.000 | 39.9 |
| t | 0 | 0.001 | 10 | 1.3e-04 | 0.00072 | 0.158 | 0.636 | 0.946 | 10.0 |
| t | 0 | 0.001 | 20 | 9.0e-05 | 0.0014 | 0.371 | 0.939 | 0.996 | 20.0 |
| t | 0 | 0.001 | 30 | 5.0e-05 | 0.00084 | 0.527 | 0.986 | 1.000 | 30.0 |
| t | 0 | 0.001 | 40 | 5.0e-05 | 0.0011 | 0.704 | 0.992 | 1.000 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00158 | 0.00016 | 0.005 | 0.533 | 0.946 | 10.0 |
| t | 0.02 | 0.01 | 20 | 9.1e-04 | 8e-05 | 0.005 | 0.806 | 0.990 | 20.0 |
| t | 0.02 | 0.01 | 30 | 7.6e-04 | 2e-05 | 0.005 | 0.925 | 1.000 | 30.0 |
| t | 0.02 | 0.01 | 40 | 5.7e-04 | 0.00014 | 0.005 | 0.973 | 1.000 | 40.0 |
| t | 0.02 | 0.001 | 10 | 1.3e-04 | <1e-12 | 0.001 | 0.339 | 0.896 | 10.0 |
| t | 0.02 | 0.001 | 20 | 7.0e-05 | <1e-12 | 0.000 | 0.686 | 0.989 | 20.0 |
| t | 0.02 | 0.001 | 30 | 5.0e-05 | <1e-12 | 0.001 | 0.878 | 1.000 | 30.0 |
| t | 0.02 | 0.001 | 40 | 5.0e-05 | <1e-12 | 0.000 | 0.952 | 1.000 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00181 | 0.0042 | 0.384 | 0.694 | 0.922 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00166 | 0.011 | 0.586 | 0.971 | 0.999 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 9.6e-04 | 0.0098 | 0.743 | 1.000 | 1.000 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 8.3e-04 | 0.01 | 0.861 | 1.000 | 1.000 | 39.9 |
| wilcoxon | 0 | 0.001 | 10 | 9.0e-05 | 8e-05 | 0.202 | 0.282 | 0.563 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 1.8e-04 | 0.001 | 0.376 | 0.833 | 0.974 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 1.0e-04 | 0.0012 | 0.564 | 0.991 | 1.000 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 7.0e-05 | 0.0014 | 0.702 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.002 | <1e-12 | 0.002 | 0.481 | 0.891 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00156 | <1e-12 | 0.005 | 0.744 | 0.997 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00105 | <1e-12 | 0.005 | 0.899 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 8.0e-04 | <1e-12 | 0.005 | 0.970 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 3.0e-05 | <1e-12 | 0.000 | 0.223 | 0.525 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 1.4e-04 | <1e-12 | 0.000 | 0.489 | 0.944 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 9.0e-05 | <1e-12 | 0.001 | 0.746 | 0.999 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 6.0e-05 | <1e-12 | 0.001 | 0.910 | 1.000 | 40.0 |

## Rules under the dev1-replay null (3610 rounds; m = 2)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 2.3e-11 | 4.7e-11 | 0.000 | 0.059 | 0.998 | 3.2 | 5.0 |
| 20 | 2.3e-11 | 4.7e-11 | 0.000 | 0.067 | 1.000 | 5.0 | 5.0 |
| 30 | 2.3e-11 | 4.7e-11 | 0.000 | 0.067 | 1.000 | 5.1 | 5.0 |
| 40 | 2.3e-11 | 4.7e-11 | 0.000 | 0.068 | 1.000 | 5.1 | 5.0 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0096 | 0.01 | 0.182 | 0.744 | 0.973 | 2.1 | 7.0 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.012 | 0.012 | 0.504 | 0.996 | 1.000 | 8.2 | 10.5 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.013 | 0.013 | 0.744 | 1.000 | 1.000 | 16.2 | 11.3 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.012 | 0.013 | 0.894 | 1.000 | 1.000 | 22.3 | 11.6 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0013 | no test at alpha/m | - | - | - | 2.1 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.00086 | 0.0012 | 0.249 | 0.969 | 1.000 | 6.3 | 14.0 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.0013 | 0.0013 | 0.501 | 1.000 | 1.000 | 12.3 | 15.2 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0013 | 0.0013 | 0.678 | 1.000 | 1.000 | 18.4 | 15.3 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.00012 | 0.00012 | 0.088 | 0.845 | 0.998 | 4.2 | 16.1 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.00013 | 0.00014 | 0.209 | 0.985 | 1.000 | 10.3 | 18.5 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.00013 | 0.00012 | 0.411 | 1.000 | 1.000 | 16.4 | 19.9 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 2.2e-05 | 9.2e-06 | 0.005 | 0.407 | 0.942 | 1.4 | 5.5 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 4.9e-06 | 1.9e-06 | 0.006 | 0.871 | 1.000 | 5.2 | 13.0 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 1.1e-06 | 4.7e-07 | 0.006 | 0.980 | 1.000 | 10.2 | 15.0 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 9.3e-07 | 3.9e-07 | 0.007 | 0.998 | 1.000 | 13.9 | 15.7 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 1.8e-07 | no test at alpha/m | - | - | - | 1.4 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 7.9e-09 | 1.5e-08 | 0.001 | 0.662 | 1.000 | 3.9 | 15.1 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 7.9e-09 | 2.9e-09 | 0.001 | 0.920 | 1.000 | 7.7 | 20.0 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 7.8e-09 | 2.9e-09 | 0.001 | 0.983 | 1.000 | 11.4 | 21.4 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 2.9e-10 | 1.1e-10 | 0.000 | 0.375 | 0.990 | 2.6 | 13.5 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 5.5e-11 | 2.5e-11 | 0.000 | 0.682 | 1.000 | 6.4 | 21.1 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 1.2e-11 | 4.7e-12 | 0.000 | 0.910 | 1.000 | 10.2 | 26.4 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 5.2e-11 | 3e-12 | 0.000 | 0.005 | 0.779 | 1.1 | 2.1 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 1.5e-12 | <1e-12 | 0.000 | 0.006 | 0.998 | 4.2 | 8.2 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.000 | 0.006 | 1.000 | 8.3 | 14.3 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.000 | 0.007 | 1.000 | 11.4 | 22.3 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | no test at alpha/m | - | - | - | 1.1 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.001 | 0.980 | 3.2 | 6.3 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.001 | 1.000 | 6.2 | 12.3 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.001 | 1.000 | 9.3 | 18.4 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.883 | 2.1 | 4.2 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.992 | 5.2 | 8.3 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 8.3 | 14.3 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.0014 | 0.0094 | 0.223 | 0.906 | 0.999 | 10.0 |
| t | 0 | 0.01 | 20 | 7.3e-04 | 0.0089 | 0.533 | 0.997 | 1.000 | 20.0 |
| t | 0 | 0.01 | 30 | 6.0e-04 | 0.011 | 0.754 | 1.000 | 1.000 | 29.9 |
| t | 0 | 0.01 | 40 | 5.1e-04 | 0.01 | 0.889 | 1.000 | 1.000 | 39.9 |
| t | 0 | 0.001 | 10 | 1.2e-04 | 0.0012 | 0.063 | 0.713 | 0.992 | 10.0 |
| t | 0 | 0.001 | 20 | 6.0e-05 | 0.0011 | 0.225 | 0.979 | 1.000 | 20.0 |
| t | 0 | 0.001 | 30 | 4.0e-05 | 0.0011 | 0.461 | 0.998 | 1.000 | 30.0 |
| t | 0 | 0.001 | 40 | 4.0e-05 | 0.0011 | 0.726 | 1.000 | 1.000 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00144 | 2e-05 | 0.005 | 0.514 | 0.994 | 10.0 |
| t | 0.02 | 0.01 | 20 | 7.8e-04 | 2e-05 | 0.005 | 0.888 | 1.000 | 20.0 |
| t | 0.02 | 0.01 | 30 | 5.8e-04 | <1e-12 | 0.005 | 0.979 | 1.000 | 30.0 |
| t | 0.02 | 0.01 | 40 | 5.1e-04 | <1e-12 | 0.005 | 0.996 | 1.000 | 40.0 |
| t | 0.02 | 0.001 | 10 | 1.3e-04 | <1e-12 | 0.001 | 0.203 | 0.961 | 10.0 |
| t | 0.02 | 0.001 | 20 | 5.0e-05 | 2e-05 | 0.000 | 0.699 | 1.000 | 20.0 |
| t | 0.02 | 0.001 | 30 | 4.0e-05 | <1e-12 | 0.000 | 0.890 | 1.000 | 30.0 |
| t | 0.02 | 0.001 | 40 | 3.0e-05 | <1e-12 | 0.001 | 0.984 | 1.000 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00396 | 0.0098 | 0.260 | 0.888 | 0.997 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00143 | 0.0095 | 0.581 | 0.998 | 1.000 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 0.00101 | 0.01 | 0.817 | 1.000 | 1.000 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 8.3e-04 | 0.0098 | 0.934 | 1.000 | 1.000 | 39.9 |
| wilcoxon | 0 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 1.4e-04 | 0.001 | 0.270 | 0.955 | 0.996 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 7.0e-05 | 0.0012 | 0.544 | 0.999 | 1.000 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 7.0e-05 | 0.00076 | 0.723 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00284 | <1e-12 | 0.004 | 0.492 | 0.983 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00144 | <1e-12 | 0.004 | 0.909 | 1.000 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00108 | <1e-12 | 0.005 | 0.990 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 7.5e-04 | <1e-12 | 0.004 | 0.999 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 1.6e-04 | <1e-12 | 0.001 | 0.688 | 0.995 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 9.0e-05 | <1e-12 | 0.001 | 0.949 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 6.0e-05 | <1e-12 | 0.000 | 0.992 | 1.000 | 40.0 |

## Rules under the dev1-ladder null (576 rounds; m = 2)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.00025 | 0.0005 | 0.002 | 0.073 | 0.724 | 3.9 | 5.4 |
| 20 | 0.00025 | 0.00051 | 0.002 | 0.083 | 0.852 | 6.4 | 6.4 |
| 30 | 0.00025 | 0.00051 | 0.002 | 0.084 | 0.885 | 7.0 | 6.8 |
| 40 | 0.00025 | 0.00051 | 0.002 | 0.084 | 0.913 | 7.8 | 7.3 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.013 | 0.013 | 0.035 | 0.166 | 0.531 | 2.4 | 4.6 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.015 | 0.016 | 0.071 | 0.421 | 0.935 | 8.5 | 13.6 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.017 | 0.017 | 0.111 | 0.632 | 0.993 | 16.6 | 20.0 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.017 | 0.018 | 0.153 | 0.797 | 1.000 | 22.7 | 25.3 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0018 | no test at alpha/m | - | - | - | 2.4 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.0012 | 0.0018 | 0.015 | 0.184 | 0.779 | 6.5 | 12.7 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.0018 | 0.0019 | 0.028 | 0.372 | 0.965 | 12.7 | 22.1 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0019 | 0.002 | 0.039 | 0.521 | 0.995 | 18.8 | 29.5 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.00018 | 0.00018 | 0.003 | 0.059 | 0.504 | 4.5 | 9.5 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.0002 | 0.00021 | 0.005 | 0.132 | 0.799 | 10.6 | 17.3 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.00021 | 0.0002 | 0.009 | 0.268 | 0.961 | 16.8 | 27.9 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00072 | 0.00052 | 0.007 | 0.064 | 0.401 | 1.6 | 3.7 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00039 | 0.00028 | 0.008 | 0.140 | 0.827 | 6.2 | 12.0 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.00022 | 0.00016 | 0.009 | 0.220 | 0.960 | 12.5 | 19.7 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.00017 | 0.00012 | 0.009 | 0.308 | 0.994 | 17.2 | 29.0 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 3.4e-05 | no test at alpha/m | - | - | - | 1.6 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 7.5e-06 | 1.1e-05 | 0.001 | 0.037 | 0.584 | 4.6 | 9.9 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 8.1e-06 | 5.5e-06 | 0.001 | 0.074 | 0.862 | 9.3 | 18.6 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 7.2e-06 | 5.2e-06 | 0.001 | 0.105 | 0.956 | 14.0 | 27.1 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 6.8e-07 | 4.9e-07 | 0.000 | 0.008 | 0.305 | 3.1 | 7.0 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 3e-07 | 2.6e-07 | 0.000 | 0.016 | 0.571 | 7.8 | 13.1 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 1.5e-07 | 1.1e-07 | 0.000 | 0.030 | 0.830 | 12.5 | 22.1 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 4.1e-05 | 2.1e-05 | 0.000 | 0.007 | 0.187 | 1.4 | 2.4 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 1.3e-05 | 6.6e-06 | 0.000 | 0.008 | 0.472 | 5.2 | 8.5 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 4.5e-06 | 2.4e-06 | 0.000 | 0.009 | 0.691 | 10.6 | 14.7 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 3.4e-06 | 1.8e-06 | 0.000 | 0.009 | 0.848 | 14.7 | 22.8 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 7.2e-07 | no test at alpha/m | - | - | - | 1.4 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 6.1e-08 | 1e-07 | 0.000 | 0.001 | 0.220 | 3.9 | 6.5 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 6.2e-08 | 3.1e-08 | 0.000 | 0.001 | 0.436 | 7.9 | 12.7 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 5.9e-08 | 3.1e-08 | 0.000 | 0.001 | 0.596 | 12.0 | 18.9 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 3.5e-09 | 1.8e-09 | 0.000 | 0.000 | 0.075 | 2.6 | 4.5 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 9.4e-10 | 5.7e-10 | 0.000 | 0.000 | 0.167 | 6.6 | 8.6 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 2.9e-10 | 1.5e-10 | 0.000 | 0.000 | 0.332 | 10.6 | 14.8 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00143 | 0.011 | 0.037 | 0.234 | 0.778 | 10.0 |
| t | 0 | 0.01 | 20 | 7.2e-04 | 0.011 | 0.057 | 0.441 | 0.977 | 20.0 |
| t | 0 | 0.01 | 30 | 6.1e-04 | 0.0099 | 0.067 | 0.595 | 0.998 | 29.9 |
| t | 0 | 0.01 | 40 | 5.0e-04 | 0.0099 | 0.096 | 0.752 | 1.000 | 39.9 |
| t | 0 | 0.001 | 10 | 1.2e-04 | 0.0011 | 0.007 | 0.069 | 0.479 | 10.0 |
| t | 0 | 0.001 | 20 | 5.0e-05 | 0.0012 | 0.011 | 0.193 | 0.892 | 20.0 |
| t | 0 | 0.001 | 30 | 4.0e-05 | 0.00086 | 0.012 | 0.303 | 0.983 | 30.0 |
| t | 0 | 0.001 | 40 | 3.0e-05 | 0.00094 | 0.017 | 0.435 | 0.998 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.0014 | 0.0018 | 0.005 | 0.084 | 0.605 | 10.0 |
| t | 0.02 | 0.01 | 20 | 7.8e-04 | 0.00088 | 0.005 | 0.133 | 0.881 | 20.0 |
| t | 0.02 | 0.01 | 30 | 5.6e-04 | 0.00066 | 0.005 | 0.198 | 0.976 | 30.0 |
| t | 0.02 | 0.01 | 40 | 5.2e-04 | 0.00072 | 0.005 | 0.254 | 0.995 | 40.0 |
| t | 0.02 | 0.001 | 10 | 1.3e-04 | 0.00014 | 0.000 | 0.013 | 0.237 | 10.0 |
| t | 0.02 | 0.001 | 20 | 6.0e-05 | 0.0001 | 0.000 | 0.032 | 0.674 | 20.0 |
| t | 0.02 | 0.001 | 30 | 5.0e-05 | 0.00012 | 0.001 | 0.062 | 0.900 | 30.0 |
| t | 0.02 | 0.001 | 40 | 4.0e-05 | 2e-05 | 0.001 | 0.090 | 0.971 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00347 | 0.0091 | 0.033 | 0.185 | 0.652 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00149 | 0.01 | 0.060 | 0.440 | 0.965 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 9.7e-04 | 0.0099 | 0.083 | 0.634 | 0.998 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 8.1e-04 | 0.01 | 0.115 | 0.803 | 1.000 | 39.9 |
| wilcoxon | 0 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 1.6e-04 | 0.00074 | 0.009 | 0.147 | 0.767 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 9.0e-05 | 0.001 | 0.017 | 0.331 | 0.971 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 7.0e-05 | 0.00084 | 0.031 | 0.561 | 0.999 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00288 | 0.00038 | 0.005 | 0.067 | 0.478 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00152 | 0.00026 | 0.004 | 0.144 | 0.873 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 9.8e-04 | 4e-05 | 0.006 | 0.233 | 0.979 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 7.7e-04 | 4e-05 | 0.005 | 0.301 | 0.997 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 1.6e-04 | <1e-12 | 0.000 | 0.039 | 0.629 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 8.0e-05 | <1e-12 | 0.001 | 0.072 | 0.886 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 6.0e-05 | <1e-12 | 0.000 | 0.115 | 0.975 | 40.0 |

## Rules under the dev1-replay-solo null (283 rounds; m = 2)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | <1e-12 | <1e-12 | 0.000 | 0.052 | 0.998 | 3.0 | 5.0 |
| 20 | <1e-12 | <1e-12 | 0.000 | 0.056 | 1.000 | 5.0 | 5.0 |
| 30 | <1e-12 | <1e-12 | 0.000 | 0.056 | 1.000 | 5.0 | 5.0 |
| 40 | <1e-12 | <1e-12 | 0.000 | 0.056 | 1.000 | 5.0 | 5.0 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.01 | 0.0095 | 0.805 | 0.814 | 0.988 | 2.7 | 7.5 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0089 | 0.0084 | 0.998 | 0.998 | 1.000 | 8.3 | 10.0 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0076 | 0.0071 | 1.000 | 1.000 | 1.000 | 15.8 | 11.0 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0068 | 0.0064 | 1.000 | 1.000 | 1.000 | 21.3 | 11.2 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.001 | no test at alpha/m | - | - | - | 2.7 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.00048 | 0.0007 | 0.977 | 0.979 | 1.000 | 6.5 | 13.6 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.00063 | 0.00058 | 1.000 | 1.000 | 1.000 | 12.1 | 14.7 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.00059 | 0.00055 | 1.000 | 1.000 | 1.000 | 17.7 | 14.8 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 6.3e-05 | 6e-05 | 0.874 | 0.878 | 1.000 | 4.6 | 16.1 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 5e-05 | 5.2e-05 | 0.989 | 0.989 | 1.000 | 10.2 | 18.2 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 4e-05 | 3.6e-05 | 1.000 | 1.000 | 1.000 | 15.8 | 19.4 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.005 | 0.814 | 0.814 | 1.1 | 7.5 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | <1e-12 | <1e-12 | 0.004 | 0.998 | 0.998 | 4.2 | 10.0 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.004 | 1.000 | 1.000 | 8.2 | 11.0 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.003 | 1.000 | 1.000 | 11.2 | 11.2 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | no test at alpha/m | - | - | - | 1.1 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.979 | 0.979 | 3.2 | 13.6 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 6.2 | 14.7 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 9.2 | 14.8 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.878 | 0.878 | 2.1 | 16.1 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.989 | 0.989 | 5.2 | 18.2 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 8.2 | 19.4 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.005 | 0.814 | 1.0 | 2.7 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | <1e-12 | <1e-12 | 0.000 | 0.004 | 0.998 | 4.0 | 8.4 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.000 | 0.004 | 1.000 | 8.0 | 13.9 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.000 | 0.003 | 1.000 | 11.0 | 21.4 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | no test at alpha/m | - | - | - | 1.0 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.979 | 3.0 | 6.5 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 6.0 | 12.1 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 9.0 | 17.7 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.878 | 2.0 | 4.6 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.989 | 5.0 | 8.4 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 8.0 | 14.0 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=2 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00143 | 0.0099 | 0.882 | 0.975 | 0.989 | 10.0 |
| t | 0 | 0.01 | 20 | 8.1e-04 | 0.01 | 0.899 | 0.988 | 1.000 | 19.9 |
| t | 0 | 0.01 | 30 | 5.8e-04 | 0.011 | 0.955 | 0.998 | 1.000 | 29.9 |
| t | 0 | 0.01 | 40 | 4.6e-04 | 0.0096 | 0.975 | 1.000 | 1.000 | 39.9 |
| t | 0 | 0.001 | 10 | 1.1e-04 | 0.0007 | 0.816 | 0.897 | 0.988 | 10.0 |
| t | 0 | 0.001 | 20 | 6.0e-05 | 0.00098 | 0.817 | 0.987 | 1.000 | 20.0 |
| t | 0 | 0.001 | 30 | 4.0e-05 | 0.0012 | 0.902 | 0.988 | 1.000 | 30.0 |
| t | 0 | 0.001 | 40 | 3.0e-05 | 0.00088 | 0.939 | 0.999 | 1.000 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00138 | <1e-12 | 0.005 | 0.902 | 0.989 | 10.0 |
| t | 0.02 | 0.01 | 20 | 7.7e-04 | <1e-12 | 0.004 | 0.970 | 1.000 | 20.0 |
| t | 0.02 | 0.01 | 30 | 5.5e-04 | <1e-12 | 0.005 | 0.986 | 1.000 | 30.0 |
| t | 0.02 | 0.01 | 40 | 4.8e-04 | <1e-12 | 0.005 | 0.989 | 1.000 | 40.0 |
| t | 0.02 | 0.001 | 10 | 1.3e-04 | <1e-12 | 0.001 | 0.868 | 0.987 | 10.0 |
| t | 0.02 | 0.001 | 20 | 6.0e-05 | <1e-12 | 0.001 | 0.945 | 0.992 | 20.0 |
| t | 0.02 | 0.001 | 30 | 5.0e-05 | <1e-12 | 0.001 | 0.982 | 1.000 | 30.0 |
| t | 0.02 | 0.001 | 40 | 4.0e-05 | <1e-12 | 0.001 | 0.987 | 1.000 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00282 | 0.0091 | 0.796 | 0.913 | 0.980 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00126 | 0.0092 | 0.930 | 1.000 | 1.000 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 9.4e-04 | 0.01 | 0.994 | 1.000 | 1.000 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 6.7e-04 | 0.01 | 1.000 | 1.000 | 1.000 | 39.9 |
| wilcoxon | 0 | 0.001 | 10 | 9.0e-05 | 0.00024 | 0.320 | 0.324 | 0.436 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 1.1e-04 | 0.00066 | 0.864 | 0.992 | 0.998 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 8.0e-05 | 0.0007 | 0.956 | 1.000 | 1.000 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 6.0e-05 | 0.0013 | 0.998 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00307 | <1e-12 | 0.005 | 0.796 | 0.966 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.0013 | <1e-12 | 0.005 | 0.932 | 1.000 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 9.2e-04 | <1e-12 | 0.005 | 0.993 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 7.4e-04 | <1e-12 | 0.005 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 1.1e-04 | <1e-12 | 0.000 | 0.324 | 0.323 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 1.6e-04 | <1e-12 | 0.000 | 0.840 | 0.995 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 7.0e-05 | <1e-12 | 0.001 | 0.970 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 6.0e-05 | <1e-12 | 0.000 | 0.994 | 1.000 | 40.0 |

