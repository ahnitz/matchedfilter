# A/A rounds of paired trials: the null, the current rule, candidate rules

x = log(t_AA / t_preference) per round: an equal challenger's log ratio. Rates are per contest, for independent rounds drawn from the measured null round by round (a process's first three contest rounds each from its own sample, later rounds and confirmations by the order's parity: Null), unless a line says otherwise; m equal challengers are taken as independent (an upper bound). Powers are for one challenger of the stated gain, its noise the A/A arm's.

## Candidate rules against D8 (no looser than the current measured false-switch rate)

False-switch rates are per contest at gain 0 for each group's m equal challengers (Holm: alpha / m per arm; the current rule with its confirmation). "Every group": the test's rate is no larger than the current rule's under each group's null; "worst": its largest rate is no larger than the current rule's largest (0.0041, dev3-joint). "With the contest effect": the same two with each group's contest effect added to both rules (an upper bound for each; the current rule's largest is then 0.018). "Keeps power": its power at 5% and 10% is at least the current rule's under every group's null, exactly; where it is not, the largest shortfall and where. Listed: every rule that meets "every group", those that meet "worst" and keep the power, and the rules compared below (the per-group rates of all are below). Power for one challenger of the gain, worst group / best group; rounds: the largest expected count at gain 0 and at 5%, and the rounds a challenger that loses every round runs (the usual case: on most banks the CPU's challengers are 1.1-2.2x slower), which with each group's cost of a round (below) is the trial's overhead.

| rule | every group | worst | with the contest effect: every / worst | keeps power | power (worst / best) 2% | power (worst / best) 5% | power (worst / best) 10% | rounds at 0 / 5% | rounds, all lost |
|---|---|---|---|---|---|---|---|---|---|
| current (TIE 5%, 75%, 5/10, confirm) | (reference) | (reference) | (reference) | (reference) | 0.000 / 0.020 | 0.029 / 0.112 | 0.210 / 1.000 | 5.8 / 6.0 | 3 |
| sign, delta 0.015, alpha 0.0001, cap 30 | yes | yes | no / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.478 | 0.001 / 1.000 | 0.008 / 1.000 | 11.0 / 21.1 | 5 |
| sign, delta 0.015, alpha 0.0001, cap 40 | yes | yes | no / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.750 | 0.001 / 1.000 | 0.014 / 1.000 | 16.8 / 31.1 | 8 |
| sign, delta 0.02, alpha 0.01, cap 20 | no | yes | no / no | no: 0.24 short at 10% (dev4-gpu-single) | 0.000 / 0.018 | 0.018 / 1.000 | 0.096 / 1.000 | 8.8 / 13.3 | 4 |
| sign, delta 0.02, alpha 0.002, cap 30 | yes | yes | no / no | no: 0.28 short at 10% (dev4-gpu-single) | 0.000 / 0.005 | 0.007 / 1.000 | 0.060 / 1.000 | 14.3 / 23.1 | 7 |
| sign, delta 0.02, alpha 0.002, cap 40 | yes | yes | no / no | no: 0.26 short at 10% (dev4-gpu-single) | 0.000 / 0.004 | 0.006 / 1.000 | 0.085 / 1.000 | 20.3 / 31.1 | 10 |
| sign, delta 0.02, alpha 0.001, cap 20 | yes | yes | no / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.002 | 0.002 / 1.000 | 0.015 / 1.000 | 7.0 / 13.5 | 3 |
| sign, delta 0.02, alpha 0.001, cap 30 | yes | yes | no / no | no: 0.31 short at 10% (dev4-gpu-single) | 0.000 / 0.002 | 0.003 / 1.000 | 0.035 / 1.000 | 12.4 / 21.0 | 6 |
| sign, delta 0.02, alpha 0.001, cap 40 | yes | yes | no / no | no: 0.29 short at 10% (dev4-gpu-single) | 0.000 / 0.003 | 0.003 / 1.000 | 0.053 / 1.000 | 18.3 / 29.7 | 9 |
| sign, delta 0.02, alpha 0.0001, cap 20 | yes | yes | no / yes | no: 0.4 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 1.000 | 0.002 / 1.000 | 5.2 / 16.5 | 2 |
| sign, delta 0.02, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.005 / 1.000 | 10.6 / 18.7 | 5 |
| sign, delta 0.02, alpha 0.0001, cap 40 | yes | yes | no / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.010 / 1.000 | 16.3 / 28.6 | 8 |
| sign, delta 0.025, alpha 0.01, cap 20 | yes | yes | no / no | no: 0.25 short at 10% (dev4-gpu-single) | 0.000 / 0.011 | 0.012 / 1.000 | 0.085 / 1.000 | 8.3 / 12.7 | 4 |
| sign, delta 0.025, alpha 0.01, cap 30 | yes | yes | no / no | no: 0.17 short at 10% (dev4-gpu-single) | 0.000 / 0.011 | 0.015 / 1.000 | 0.173 / 1.000 | 15.8 / 22.7 | 8 |
| sign, delta 0.025, alpha 0.01, cap 40 | yes | yes | no / no | no: 0.095 short at 5% (dev2-joint) | 0.000 / 0.010 | 0.017 / 1.000 | 0.249 / 1.000 | 21.5 / 29.4 | 11 |
| sign, delta 0.025, alpha 0.005, cap 10 | yes | yes | no / yes | no: 0.38 short at 10% (dev3-gpu-single) | 0.000 / 0.005 | 0.000 / 1.000 | 0.009 / 1.000 | 2.7 / 10.0 | 1 |
| sign, delta 0.025, alpha 0.005, cap 20 | yes | yes | no / yes | no: 0.29 short at 10% (dev4-gpu-single) | 0.000 / 0.006 | 0.006 / 1.000 | 0.055 / 1.000 | 8.3 / 13.0 | 4 |
| sign, delta 0.025, alpha 0.005, cap 30 | yes | yes | no / no | no: 0.24 short at 10% (dev4-gpu-single) | 0.000 / 0.005 | 0.006 / 1.000 | 0.097 / 1.000 | 13.8 / 21.1 | 7 |
| sign, delta 0.025, alpha 0.005, cap 40 | yes | yes | no / no | no: 0.18 short at 10% (dev4-gpu-single) | 0.000 / 0.005 | 0.006 / 1.000 | 0.163 / 1.000 | 21.5 / 31.4 | 11 |
| sign, delta 0.025, alpha 0.003, cap 10 | yes | yes | no / yes | no: 0.4 short at 10% (dev3-gpu-single) | 0.000 / 0.003 | 0.000 / 1.000 | 0.008 / 1.000 | 2.7 / 10.0 | 1 |
| sign, delta 0.025, alpha 0.003, cap 20 | yes | yes | no / yes | no: 0.3 short at 10% (dev4-gpu-single) | 0.000 / 0.003 | 0.003 / 1.000 | 0.040 / 1.000 | 8.3 / 13.3 | 4 |
| sign, delta 0.025, alpha 0.003, cap 30 | yes | yes | no / no | no: 0.28 short at 10% (dev4-gpu-single) | 0.000 / 0.003 | 0.003 / 1.000 | 0.065 / 1.000 | 13.8 / 21.7 | 7 |
| sign, delta 0.025, alpha 0.003, cap 40 | yes | yes | no / no | no: 0.23 short at 10% (dev4-gpu-single) | 0.000 / 0.003 | 0.003 / 1.000 | 0.108 / 1.000 | 19.6 / 29.6 | 10 |
| sign, delta 0.025, alpha 0.002, cap 20 | yes | yes | no / yes | no: 0.32 short at 10% (dev4-gpu-single) | 0.000 / 0.002 | 0.001 / 1.000 | 0.019 / 1.000 | 6.6 / 12.8 | 3 |
| sign, delta 0.025, alpha 0.002, cap 30 | yes | yes | no / yes | no: 0.29 short at 10% (dev4-gpu-single) | 0.000 / 0.002 | 0.002 / 1.000 | 0.054 / 1.000 | 13.8 / 21.8 | 7 |
| sign, delta 0.025, alpha 0.002, cap 40 | yes | yes | no / no | no: 0.26 short at 10% (dev4-gpu-single) | 0.000 / 0.002 | 0.002 / 1.000 | 0.078 / 1.000 | 19.6 / 30.2 | 10 |
| sign, delta 0.025, alpha 0.001, cap 20 | yes | yes | no / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.001 / 1.000 | 0.013 / 1.000 | 6.6 / 13.6 | 3 |
| sign, delta 0.025, alpha 0.001, cap 30 | yes | yes | no / yes | no: 0.31 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.001 / 1.000 | 0.031 / 1.000 | 11.9 / 19.3 | 6 |
| sign, delta 0.025, alpha 0.001, cap 40 | yes | yes | no / no | no: 0.29 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.001 / 1.000 | 0.048 / 1.000 | 17.7 / 28.2 | 9 |
| sign, delta 0.025, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.45 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 1.000 | 0.002 / 1.000 | 4.9 / 16.7 | 2 |
| sign, delta 0.025, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.34 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.005 / 1.000 | 10.1 / 18.2 | 5 |
| sign, delta 0.025, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.009 / 1.000 | 15.8 / 25.5 | 8 |
| sign, delta 0.03, alpha 0.02, cap 40 | yes | yes | no / no | no: 0.089 short at 5% (dev2-joint) | 0.000 / 0.013 | 0.023 / 1.000 | 0.355 / 1.000 | 23.0 / 30.4 | 12 |
| sign, delta 0.03, alpha 0.01, cap 20 | yes | yes | no / yes | no: 0.26 short at 10% (dev4-gpu-single) | 0.000 / 0.007 | 0.008 / 1.000 | 0.078 / 1.000 | 8.1 / 11.9 | 4 |
| sign, delta 0.03, alpha 0.01, cap 30 | yes | yes | no / no | no: 0.18 short at 10% (dev4-gpu-single) | 0.000 / 0.006 | 0.009 / 1.000 | 0.163 / 1.000 | 15.5 / 21.7 | 8 |
| sign, delta 0.03, alpha 0.01, cap 40 | yes | yes | no / no | no: 0.1 short at 10% (dev4-gpu-single) | 0.000 / 0.006 | 0.010 / 1.000 | 0.238 / 1.000 | 21.1 / 29.0 | 11 |
| sign, delta 0.03, alpha 0.005, cap 10 | yes | yes | yes / yes | no: 0.44 short at 10% (dev3-gpu-single) | 0.000 / 0.004 | 0.000 / 1.000 | 0.008 / 1.000 | 2.4 / 10.0 | 1 |
| sign, delta 0.03, alpha 0.005, cap 20 | yes | yes | no / yes | no: 0.29 short at 10% (dev4-gpu-single) | 0.000 / 0.003 | 0.005 / 1.000 | 0.050 / 1.000 | 8.1 / 12.2 | 4 |
| sign, delta 0.03, alpha 0.005, cap 30 | yes | yes | no / yes | no: 0.25 short at 10% (dev4-gpu-single) | 0.000 / 0.003 | 0.004 / 1.000 | 0.091 / 1.000 | 13.7 / 19.5 | 7 |
| sign, delta 0.03, alpha 0.005, cap 40 | yes | yes | no / no | no: 0.19 short at 10% (dev4-gpu-single) | 0.000 / 0.003 | 0.003 / 1.000 | 0.155 / 1.000 | 21.1 / 29.7 | 11 |
| sign, delta 0.03, alpha 0.003, cap 10 | yes | yes | yes / yes | no: 0.46 short at 10% (dev3-gpu-single) | 0.000 / 0.002 | 0.000 / 1.000 | 0.008 / 1.000 | 2.4 / 10.0 | 1 |
| sign, delta 0.03, alpha 0.003, cap 20 | yes | yes | yes / yes | no: 0.3 short at 10% (dev4-gpu-single) | 0.000 / 0.002 | 0.002 / 1.000 | 0.036 / 1.000 | 8.1 / 13.5 | 4 |
| sign, delta 0.03, alpha 0.003, cap 30 | yes | yes | no / yes | no: 0.28 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.002 / 1.000 | 0.061 / 1.000 | 13.7 / 19.6 | 7 |
| sign, delta 0.03, alpha 0.003, cap 40 | yes | yes | no / no | no: 0.24 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.002 / 1.000 | 0.102 / 1.000 | 19.3 / 27.3 | 10 |
| sign, delta 0.03, alpha 0.002, cap 20 | yes | yes | yes / yes | no: 0.32 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.001 / 1.000 | 0.017 / 1.000 | 6.3 / 13.5 | 3 |
| sign, delta 0.03, alpha 0.002, cap 30 | yes | yes | no / yes | no: 0.29 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.001 / 1.000 | 0.050 / 1.000 | 13.7 / 19.7 | 7 |
| sign, delta 0.03, alpha 0.002, cap 40 | yes | yes | no / yes | no: 0.27 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.001 / 1.000 | 0.074 / 1.000 | 19.3 / 27.4 | 10 |
| sign, delta 0.03, alpha 0.001, cap 20 | yes | yes | yes / yes | no: 0.34 short at 10% (dev2-gpu-kernels) | 0.000 / 0.000 | 0.000 / 1.000 | 0.012 / 1.000 | 6.3 / 13.8 | 3 |
| sign, delta 0.03, alpha 0.001, cap 30 | yes | yes | yes / yes | no: 0.31 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.029 / 1.000 | 11.8 / 17.2 | 6 |
| sign, delta 0.03, alpha 0.001, cap 40 | yes | yes | no / yes | no: 0.29 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.045 / 1.000 | 17.4 / 27.3 | 9 |
| sign, delta 0.03, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.5 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 1.000 | 0.002 / 1.000 | 4.7 / 16.7 | 2 |
| sign, delta 0.03, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.34 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.004 / 1.000 | 10.0 / 19.5 | 5 |
| sign, delta 0.03, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.008 / 1.000 | 15.5 / 22.4 | 8 |
| sign, delta 0.04, alpha 0.02, cap 20 | yes | yes | yes / yes | no: 0.2 short at 10% (dev4-gpu-single) | 0.000 / 0.006 | 0.014 / 0.998 | 0.145 / 1.000 | 9.6 / 13.3 | 5 |
| sign, delta 0.04, alpha 0.02, cap 30 | yes | yes | no / no | no: 0.13 short at 10% (dev4-gpu-single) | 0.000 / 0.004 | 0.008 / 1.000 | 0.208 / 1.000 | 14.9 / 19.3 | 8 |
| sign, delta 0.04, alpha 0.02, cap 40 | yes | yes | no / no | no: 0.1 short at 5% (dev2-joint) | 0.000 / 0.003 | 0.008 / 1.000 | 0.325 / 1.000 | 22.0 / 28.9 | 12 |
| sign, delta 0.04, alpha 0.01, cap 10 | yes | yes | yes / yes | no: 0.44 short at 10% (dev2-gpu-kernels) | 0.000 / 0.004 | 0.000 / 0.743 | 0.012 / 1.000 | 2.1 / 7.9 | 1 |
| sign, delta 0.04, alpha 0.01, cap 20 | yes | yes | yes / yes | no: 0.27 short at 10% (dev4-gpu-single) | 0.000 / 0.002 | 0.003 / 0.997 | 0.071 / 1.000 | 7.8 / 14.4 | 4 |
| sign, delta 0.04, alpha 0.01, cap 30 | yes | yes | no / yes | no: 0.19 short at 10% (dev4-gpu-single) | 0.000 / 0.002 | 0.003 / 1.000 | 0.146 / 1.000 | 14.9 / 19.5 | 8 |
| sign, delta 0.04, alpha 0.01, cap 40 | yes | yes | no / no | no: 0.13 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.003 / 1.000 | 0.213 / 1.000 | 20.2 / 26.7 | 11 |
| sign, delta 0.04, alpha 0.005, cap 10 | yes | yes | yes / yes | no: 0.48 short at 10% (dev3-gpu-single) | 0.000 / 0.002 | 0.000 / 0.728 | 0.006 / 1.000 | 2.1 / 8.7 | 1 |
| sign, delta 0.04, alpha 0.005, cap 20 | yes | yes | yes / yes | no: 0.3 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.002 / 0.985 | 0.044 / 1.000 | 7.8 / 12.8 | 4 |
| sign, delta 0.04, alpha 0.005, cap 30 | yes | yes | yes / yes | no: 0.26 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.001 / 1.000 | 0.080 / 1.000 | 13.1 / 19.8 | 7 |
| sign, delta 0.04, alpha 0.005, cap 40 | yes | yes | no / yes | no: 0.2 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.001 / 1.000 | 0.135 / 1.000 | 20.2 / 26.8 | 11 |
| sign, delta 0.04, alpha 0.003, cap 10 | yes | yes | yes / yes | no: 0.51 short at 10% (dev3-gpu-single) | 0.000 / 0.001 | 0.000 / 0.728 | 0.006 / 1.000 | 2.1 / 8.7 | 1 |
| sign, delta 0.04, alpha 0.003, cap 20 | yes | yes | yes / yes | no: 0.31 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.980 | 0.032 / 1.000 | 7.8 / 13.7 | 4 |
| sign, delta 0.04, alpha 0.003, cap 30 | yes | yes | yes / yes | no: 0.29 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.052 / 1.000 | 13.1 / 20.8 | 7 |
| sign, delta 0.04, alpha 0.003, cap 40 | yes | yes | yes / yes | no: 0.25 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.088 / 1.000 | 18.4 / 24.6 | 10 |
| sign, delta 0.04, alpha 0.002, cap 20 | yes | yes | yes / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.980 | 0.015 / 1.000 | 6.0 / 13.7 | 3 |
| sign, delta 0.04, alpha 0.002, cap 30 | yes | yes | yes / yes | no: 0.3 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.043 / 1.000 | 13.1 / 22.0 | 7 |
| sign, delta 0.04, alpha 0.002, cap 40 | yes | yes | yes / yes | no: 0.28 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.063 / 1.000 | 18.4 / 25.8 | 10 |
| sign, delta 0.04, alpha 0.001, cap 20 | yes | yes | yes / yes | no: 0.44 short at 10% (dev2-gpu-kernels) | 0.000 / 0.000 | 0.000 / 0.903 | 0.010 / 1.000 | 6.0 / 13.8 | 3 |
| sign, delta 0.04, alpha 0.001, cap 30 | yes | yes | yes / yes | no: 0.32 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.999 | 0.024 / 1.000 | 11.3 / 20.8 | 6 |
| sign, delta 0.04, alpha 0.001, cap 40 | yes | yes | yes / yes | no: 0.3 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.038 / 1.000 | 16.7 / 27.8 | 9 |
| sign, delta 0.04, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.57 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 0.875 | 0.001 / 1.000 | 4.2 / 16.7 | 2 |
| sign, delta 0.04, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.37 short at 10% (dev2-gpu-kernels) | 0.000 / 0.000 | 0.000 / 0.990 | 0.004 / 1.000 | 9.6 / 20.2 | 5 |
| sign, delta 0.04, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.33 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 1.000 | 0.006 / 1.000 | 14.9 / 29.7 | 8 |
| sign, delta 0.05, alpha 0.05, cap 40 | yes | yes | no / no | no: 0.092 short at 5% (dev2-joint) | 0.000 / 0.005 | 0.003 / 0.089 | 0.444 / 1.000 | 22.8 / 29.4 | 13 |
| sign, delta 0.05, alpha 0.02, cap 10 | yes | yes | yes / yes | no: 0.48 short at 10% (dev2-gpu-kernels) | 0.000 / 0.004 | 0.002 / 0.028 | 0.040 / 1.000 | 4.1 / 5.6 | 2 |
| sign, delta 0.05, alpha 0.02, cap 20 | yes | yes | yes / yes | no: 0.24 short at 10% (dev2-gpu-kernels) | 0.000 / 0.003 | 0.002 / 0.036 | 0.111 / 1.000 | 9.2 / 11.6 | 5 |
| sign, delta 0.05, alpha 0.02, cap 30 | yes | yes | yes / yes | no: 0.18 short at 10% (dev4-gpu-single) | 0.000 / 0.002 | 0.001 / 0.038 | 0.163 / 1.000 | 14.3 / 18.4 | 8 |
| sign, delta 0.05, alpha 0.02, cap 40 | yes | yes | no / no | no: 0.11 short at 5% (dev2-joint) | 0.000 / 0.002 | 0.001 / 0.041 | 0.264 / 1.000 | 21.1 / 27.5 | 12 |
| sign, delta 0.05, alpha 0.01, cap 10 | yes | yes | yes / yes | no: 0.51 short at 10% (dev2-gpu-kernels) | 0.000 / 0.003 | 0.000 / 0.016 | 0.010 / 1.000 | 2.0 / 3.7 | 1 |
| sign, delta 0.05, alpha 0.01, cap 20 | yes | yes | yes / yes | no: 0.29 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.000 / 0.018 | 0.052 / 1.000 | 7.5 / 9.7 | 4 |
| sign, delta 0.05, alpha 0.01, cap 30 | yes | yes | yes / yes | no: 0.23 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.000 / 0.021 | 0.111 / 1.000 | 14.3 / 18.4 | 8 |
| sign, delta 0.05, alpha 0.01, cap 40 | yes | yes | yes / yes | no: 0.17 short at 10% (dev4-gpu-single) | 0.000 / 0.001 | 0.000 / 0.022 | 0.165 / 1.000 | 19.4 / 25.3 | 11 |
| sign, delta 0.05, alpha 0.005, cap 10 | yes | yes | yes / yes | no: 0.59 short at 10% (dev2-joint) | 0.000 / 0.001 | 0.000 / 0.008 | 0.004 / 1.000 | 2.0 / 3.7 | 1 |
| sign, delta 0.05, alpha 0.005, cap 20 | yes | yes | yes / yes | no: 0.4 short at 10% (dev2-gpu-kernels) | 0.000 / 0.000 | 0.000 / 0.010 | 0.031 / 1.000 | 7.5 / 9.7 | 4 |
| sign, delta 0.05, alpha 0.005, cap 30 | yes | yes | yes / yes | no: 0.28 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.011 | 0.058 / 1.000 | 12.6 / 16.2 | 7 |
| sign, delta 0.05, alpha 0.005, cap 40 | yes | yes | yes / yes | no: 0.24 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.011 | 0.100 / 1.000 | 19.4 / 25.3 | 11 |
| sign, delta 0.05, alpha 0.003, cap 10 | yes | yes | yes / yes | no: 0.6 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 0.004 | 0.004 / 1.000 | 2.0 / 3.7 | 1 |
| sign, delta 0.05, alpha 0.003, cap 20 | yes | yes | yes / yes | no: 0.44 short at 10% (dev2-gpu-kernels) | 0.000 / 0.000 | 0.000 / 0.006 | 0.022 / 1.000 | 7.5 / 9.7 | 4 |
| sign, delta 0.05, alpha 0.003, cap 30 | yes | yes | yes / yes | no: 0.3 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.006 | 0.037 / 1.000 | 12.6 / 16.2 | 7 |
| sign, delta 0.05, alpha 0.003, cap 40 | yes | yes | yes / yes | no: 0.28 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.007 | 0.063 / 1.000 | 17.7 / 23.0 | 10 |
| sign, delta 0.05, alpha 0.002, cap 20 | yes | yes | yes / yes | no: 0.52 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 0.004 | 0.010 / 1.000 | 5.9 / 7.7 | 3 |
| sign, delta 0.05, alpha 0.002, cap 30 | yes | yes | yes / yes | no: 0.31 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.005 | 0.029 / 1.000 | 12.6 / 16.2 | 7 |
| sign, delta 0.05, alpha 0.002, cap 40 | yes | yes | yes / yes | no: 0.3 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.004 | 0.043 / 1.000 | 17.7 / 23.0 | 10 |
| sign, delta 0.05, alpha 0.001, cap 20 | yes | yes | yes / yes | no: 0.56 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 0.002 | 0.007 / 1.000 | 5.9 / 7.7 | 3 |
| sign, delta 0.05, alpha 0.001, cap 30 | yes | yes | yes / yes | no: 0.39 short at 10% (dev2-gpu-kernels) | 0.000 / 0.000 | 0.000 / 0.002 | 0.016 / 1.000 | 10.9 / 13.9 | 6 |
| sign, delta 0.05, alpha 0.001, cap 40 | yes | yes | yes / yes | no: 0.31 short at 10% (dev4-gpu-single) | 0.000 / 0.000 | 0.000 / 0.003 | 0.025 / 1.000 | 16.0 / 20.8 | 9 |
| sign, delta 0.05, alpha 0.0001, cap 20 | yes | yes | yes / yes | no: 0.68 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 0.000 | 0.001 / 1.000 | 4.1 / 5.7 | 2 |
| sign, delta 0.05, alpha 0.0001, cap 30 | yes | yes | yes / yes | no: 0.59 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 1.000 | 9.2 / 11.7 | 5 |
| sign, delta 0.05, alpha 0.0001, cap 40 | yes | yes | yes / yes | no: 0.48 short at 10% (dev2-joint) | 0.000 / 0.000 | 0.000 / 0.000 | 0.004 / 1.000 | 14.3 / 18.5 | 8 |

The cost of a round, per group: the mean over its rounds of every run but the preference's timed one (each configuration is settled and timed: twice its time; the A/A arm, a diagnostic, left out): dev2-joint 0.00382 s; dev2-gpu-single 0.0126 s; dev2-gpu-kernels 0.0627 s; dev3-joint 0.0309 s; dev3-gpu-single 0.0282 s; dev3-gpu-kernels 0.485 s; dev4-joint 0.038 s; dev4-gpu-single 0.0199 s; dev4-gpu-kernels 0.801 s.

Per group, for every candidate that exists at alpha / m within its cap (false-switch rate, the current rule's, and both with the group's contest effect added):

| rule | dev2-joint | dev2-gpu-single | dev2-gpu-kernels | dev3-joint | dev3-gpu-single | dev3-gpu-kernels | dev4-joint | dev4-gpu-single | dev4-gpu-kernels |
|---|---|---|---|---|---|---|---|---|---|
| delta 0, alpha 0.05, cap 10 | 0.084 vs 0.0011 (0.084 vs 0.0011) | 0.014 vs 0.00062 (0.03 vs 0.018) | 0.032 vs 0.00016 (0.16 vs 0.0073) | 0.0094 vs 0.0041 (0.0094 vs 0.0041) | 0.076 vs 0.0019 (0.076 vs 0.0019) | 0.075 vs <1e-12 (0.095 vs <1e-12) | 0.02 vs 5.1e-09 (0.02 vs 5.1e-09) | 0.023 vs 0.00091 (0.023 vs 0.00091) | 0.045 vs <1e-12 (0.045 vs <1e-12) |
| delta 0, alpha 0.05, cap 20 | 0.03 vs 0.0011 (0.03 vs 0.0011) | 0.023 vs 0.00062 (0.086 vs 0.018) | 0.03 vs 0.00016 (0.24 vs 0.0073) | 0.025 vs 0.0041 (0.025 vs 0.0041) | 0.079 vs 0.0019 (0.079 vs 0.0019) | 0.093 vs <1e-12 (0.13 vs <1e-12) | 0.0053 vs 5.1e-09 (0.0053 vs 5.1e-09) | 0.022 vs 0.00091 (0.022 vs 0.00091) | 0.048 vs <1e-12 (0.048 vs <1e-12) |
| delta 0, alpha 0.05, cap 30 | 0.024 vs 0.0011 (0.024 vs 0.0011) | 0.028 vs 0.00062 (0.14 vs 0.018) | 0.031 vs 0.00016 (0.28 vs 0.0073) | 0.038 vs 0.0041 (0.038 vs 0.0041) | 0.088 vs 0.0019 (0.088 vs 0.0019) | 0.11 vs <1e-12 (0.17 vs <1e-12) | 0.0038 vs 5.1e-09 (0.0038 vs 5.1e-09) | 0.031 vs 0.00091 (0.031 vs 0.00091) | 0.052 vs <1e-12 (0.052 vs <1e-12) |
| delta 0, alpha 0.05, cap 40 | 0.02 vs 0.0011 (0.02 vs 0.0011) | 0.031 vs 0.00062 (0.18 vs 0.018) | 0.029 vs 0.00016 (0.32 vs 0.0073) | 0.044 vs 0.0041 (0.044 vs 0.0041) | 0.089 vs 0.0019 (0.089 vs 0.0019) | 0.12 vs <1e-12 (0.2 vs <1e-12) | 0.0031 vs 5.1e-09 (0.0031 vs 5.1e-09) | 0.036 vs 0.00091 (0.036 vs 0.00091) | 0.054 vs <1e-12 (0.054 vs <1e-12) |
| delta 0, alpha 0.02, cap 10 | 0.01 vs 0.0011 (0.01 vs 0.0011) | 0.0056 vs 0.00062 (0.02 vs 0.018) | 0.008 vs 0.00016 (0.062 vs 0.0073) | 0.0024 vs 0.0041 (0.0024 vs 0.0041) | 0.028 vs 0.0019 (0.028 vs 0.0019) | 0.022 vs <1e-12 (0.031 vs <1e-12) | 0.0017 vs 5.1e-09 (0.0017 vs 5.1e-09) | 0.0043 vs 0.00091 (0.0043 vs 0.00091) | 0.012 vs <1e-12 (0.012 vs <1e-12) |
| delta 0, alpha 0.02, cap 20 | 0.011 vs 0.0011 (0.011 vs 0.0011) | 0.0084 vs 0.00062 (0.055 vs 0.018) | 0.012 vs 0.00016 (0.16 vs 0.0073) | 0.007 vs 0.0041 (0.007 vs 0.0041) | 0.036 vs 0.0019 (0.036 vs 0.0019) | 0.04 vs <1e-12 (0.068 vs <1e-12) | 0.0018 vs 5.1e-09 (0.0018 vs 5.1e-09) | 0.0072 vs 0.00091 (0.0072 vs 0.00091) | 0.019 vs <1e-12 (0.019 vs <1e-12) |
| delta 0, alpha 0.02, cap 30 | 0.0055 vs 0.0011 (0.0055 vs 0.0011) | 0.011 vs 0.00062 (0.092 vs 0.018) | 0.012 vs 0.00016 (0.21 vs 0.0073) | 0.011 vs 0.0041 (0.011 vs 0.0041) | 0.038 vs 0.0019 (0.038 vs 0.0019) | 0.047 vs <1e-12 (0.093 vs <1e-12) | 0.00065 vs 5.1e-09 (0.00065 vs 5.1e-09) | 0.0081 vs 0.00091 (0.0081 vs 0.00091) | 0.02 vs <1e-12 (0.02 vs <1e-12) |
| delta 0, alpha 0.02, cap 40 | 0.0052 vs 0.0011 (0.0052 vs 0.0011) | 0.012 vs 0.00062 (0.13 vs 0.018) | 0.01 vs 0.00016 (0.27 vs 0.0073) | 0.015 vs 0.0041 (0.015 vs 0.0041) | 0.041 vs 0.0019 (0.041 vs 0.0019) | 0.056 vs <1e-12 (0.12 vs <1e-12) | 0.0006 vs 5.1e-09 (0.0006 vs 5.1e-09) | 0.011 vs 0.00091 (0.011 vs 0.00091) | 0.021 vs <1e-12 (0.021 vs <1e-12) |
| delta 0, alpha 0.01, cap 10 | 0.0086 vs 0.0011 (0.0086 vs 0.0011) | 0.0022 vs 0.00062 (0.0052 vs 0.018) | 0.0042 vs 0.00016 (0.046 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.016 vs 0.0019 (0.016 vs 0.0019) | 0.011 vs <1e-12 (0.018 vs <1e-12) | 0.0014 vs 5.1e-09 (0.0014 vs 5.1e-09) | 0.0027 vs 0.00091 (0.0027 vs 0.00091) | 0.0058 vs <1e-12 (0.0058 vs <1e-12) |
| delta 0, alpha 0.01, cap 20 | 0.0021 vs 0.0011 (0.0021 vs 0.0011) | 0.0041 vs 0.00062 (0.033 vs 0.018) | 0.0061 vs 0.00016 (0.13 vs 0.0073) | 0.0026 vs 0.0041 (0.0026 vs 0.0041) | 0.018 vs 0.0019 (0.018 vs 0.0019) | 0.024 vs <1e-12 (0.048 vs <1e-12) | 0.00022 vs 5.1e-09 (0.00022 vs 5.1e-09) | 0.0022 vs 0.00091 (0.0022 vs 0.00091) | 0.011 vs <1e-12 (0.011 vs <1e-12) |
| delta 0, alpha 0.01, cap 30 | 0.002 vs 0.0011 (0.002 vs 0.0011) | 0.0054 vs 0.00062 (0.073 vs 0.018) | 0.0054 vs 0.00016 (0.18 vs 0.0073) | 0.0052 vs 0.0041 (0.0052 vs 0.0041) | 0.021 vs 0.0019 (0.021 vs 0.0019) | 0.027 vs <1e-12 (0.066 vs <1e-12) | 0.0002 vs 5.1e-09 (0.0002 vs 5.1e-09) | 0.0035 vs 0.00091 (0.0035 vs 0.00091) | 0.011 vs <1e-12 (0.011 vs <1e-12) |
| delta 0, alpha 0.01, cap 40 | 0.0019 vs 0.0011 (0.0019 vs 0.0011) | 0.0057 vs 0.00062 (0.1 vs 0.018) | 0.0051 vs 0.00016 (0.23 vs 0.0073) | 0.0066 vs 0.0041 (0.0066 vs 0.0041) | 0.022 vs 0.0019 (0.022 vs 0.0019) | 0.032 vs <1e-12 (0.085 vs <1e-12) | 0.00019 vs 5.1e-09 (0.00019 vs 5.1e-09) | 0.0044 vs 0.00091 (0.0044 vs 0.00091) | 0.011 vs <1e-12 (0.011 vs <1e-12) |
| delta 0, alpha 0.005, cap 10 | 0.0011 vs 0.0011 (0.0011 vs 0.0011) | 0.0012 vs 0.00062 (0.0037 vs 0.018) | 0.0018 vs 0.00016 (0.032 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0076 vs 0.0019 (0.0076 vs 0.0019) | 0.0064 vs <1e-12 (0.011 vs <1e-12) | 0.00012 vs 5.1e-09 (0.00012 vs 5.1e-09) | 0.0005 vs 0.00091 (0.0005 vs 0.00091) | 0.0032 vs <1e-12 (0.0032 vs <1e-12) |
| delta 0, alpha 0.005, cap 20 | 0.0013 vs 0.0011 (0.0013 vs 0.0011) | 0.0019 vs 0.00062 (0.023 vs 0.018) | 0.0026 vs 0.00016 (0.08 vs 0.0073) | 0.00097 vs 0.0041 (0.00097 vs 0.0041) | 0.0099 vs 0.0019 (0.0099 vs 0.0019) | 0.011 vs <1e-12 (0.026 vs <1e-12) | 0.00014 vs 5.1e-09 (0.00014 vs 5.1e-09) | 0.0011 vs 0.00091 (0.0011 vs 0.00091) | 0.0049 vs <1e-12 (0.0049 vs <1e-12) |
| delta 0, alpha 0.005, cap 30 | 0.00066 vs 0.0011 (0.00066 vs 0.0011) | 0.0025 vs 0.00062 (0.05 vs 0.018) | 0.0026 vs 0.00016 (0.13 vs 0.0073) | 0.002 vs 0.0041 (0.002 vs 0.0041) | 0.011 vs 0.0019 (0.011 vs 0.0019) | 0.014 vs <1e-12 (0.04 vs <1e-12) | 5.3e-05 vs 5.1e-09 (5.3e-05 vs 5.1e-09) | 0.0013 vs 0.00091 (0.0013 vs 0.00091) | 0.0051 vs <1e-12 (0.0051 vs <1e-12) |
| delta 0, alpha 0.005, cap 40 | 0.0004 vs 0.0011 (0.0004 vs 0.0011) | 0.0028 vs 0.00062 (0.08 vs 0.018) | 0.0024 vs 0.00016 (0.19 vs 0.0073) | 0.0026 vs 0.0041 (0.0026 vs 0.0041) | 0.011 vs 0.0019 (0.011 vs 0.0019) | 0.018 vs <1e-12 (0.062 vs <1e-12) | 2.6e-05 vs 5.1e-09 (2.6e-05 vs 5.1e-09) | 0.0015 vs 0.00091 (0.0015 vs 0.00091) | 0.0056 vs <1e-12 (0.0056 vs <1e-12) |
| delta 0, alpha 0.003, cap 10 | 0.00097 vs 0.0011 (0.00097 vs 0.0011) | 0.00055 vs 0.00062 (0.0024 vs 0.018) | 0.0018 vs 0.00016 (0.032 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0043 vs 0.0019 (0.0043 vs 0.0019) | 0.0064 vs <1e-12 (0.011 vs <1e-12) | 0.00011 vs 5.1e-09 (0.00011 vs 5.1e-09) | 0.00047 vs 0.00091 (0.00047 vs 0.00091) | 0.0032 vs <1e-12 (0.0032 vs <1e-12) |
| delta 0, alpha 0.003, cap 20 | 0.0003 vs 0.0011 (0.0003 vs 0.0011) | 0.0013 vs 0.00062 (0.02 vs 0.018) | 0.0011 vs 0.00016 (0.06 vs 0.0073) | 0.00067 vs 0.0041 (0.00067 vs 0.0041) | 0.0061 vs 0.0019 (0.0061 vs 0.0019) | 0.0055 vs <1e-12 (0.015 vs <1e-12) | 2.1e-05 vs 5.1e-09 (2.1e-05 vs 5.1e-09) | 0.00048 vs 0.00091 (0.00048 vs 0.00091) | 0.0021 vs <1e-12 (0.0021 vs <1e-12) |
| delta 0, alpha 0.003, cap 30 | 0.00023 vs 0.0011 (0.00023 vs 0.0011) | 0.0013 vs 0.00062 (0.039 vs 0.018) | 0.0015 vs 0.00016 (0.12 vs 0.0073) | 0.00088 vs 0.0041 (0.00088 vs 0.0041) | 0.0061 vs 0.0019 (0.0061 vs 0.0019) | 0.0092 vs <1e-12 (0.031 vs <1e-12) | 1.5e-05 vs 5.1e-09 (1.5e-05 vs 5.1e-09) | 0.00052 vs 0.00091 (0.00052 vs 0.00091) | 0.0032 vs <1e-12 (0.0032 vs <1e-12) |
| delta 0, alpha 0.003, cap 40 | 0.00024 vs 0.0011 (0.00024 vs 0.0011) | 0.0016 vs 0.00062 (0.063 vs 0.018) | 0.0014 vs 0.00016 (0.16 vs 0.0073) | 0.0013 vs 0.0041 (0.0013 vs 0.0041) | 0.0071 vs 0.0019 (0.0071 vs 0.0019) | 0.011 vs <1e-12 (0.043 vs <1e-12) | 1.6e-05 vs 5.1e-09 (1.6e-05 vs 5.1e-09) | 0.00073 vs 0.00091 (0.00073 vs 0.00091) | 0.0034 vs <1e-12 (0.0034 vs <1e-12) |
| delta 0, alpha 0.002, cap 20 | 0.00018 vs 0.0011 (0.00018 vs 0.0011) | 0.00075 vs 0.00062 (0.01 vs 0.018) | 0.0011 vs 0.00016 (0.06 vs 0.0073) | 0.00019 vs 0.0041 (0.00019 vs 0.0041) | 0.0041 vs 0.0019 (0.0041 vs 0.0019) | 0.0055 vs <1e-12 (0.015 vs <1e-12) | 1.3e-05 vs 5.1e-09 (1.3e-05 vs 5.1e-09) | 0.0002 vs 0.00091 (0.0002 vs 0.00091) | 0.0021 vs <1e-12 (0.0021 vs <1e-12) |
| delta 0, alpha 0.002, cap 30 | 0.00018 vs 0.0011 (0.00018 vs 0.0011) | 0.00099 vs 0.00062 (0.036 vs 0.018) | 0.0008 vs 0.00016 (0.098 vs 0.0073) | 0.00059 vs 0.0041 (0.00059 vs 0.0041) | 0.0048 vs 0.0019 (0.0048 vs 0.0019) | 0.0057 vs <1e-12 (0.023 vs <1e-12) | 1.3e-05 vs 5.1e-09 (1.3e-05 vs 5.1e-09) | 0.00036 vs 0.00091 (0.00036 vs 0.00091) | 0.0018 vs <1e-12 (0.0018 vs <1e-12) |
| delta 0, alpha 0.002, cap 40 | 6.6e-05 vs 0.0011 (6.6e-05 vs 0.0011) | 0.00092 vs 0.00062 (0.052 vs 0.018) | 0.0009 vs 0.00016 (0.15 vs 0.0073) | 0.00072 vs 0.0041 (0.00072 vs 0.0041) | 0.0042 vs 0.0019 (0.0042 vs 0.0019) | 0.0076 vs <1e-12 (0.036 vs <1e-12) | 2.9e-06 vs 5.1e-09 (2.9e-06 vs 5.1e-09) | 0.00034 vs 0.00091 (0.00034 vs 0.00091) | 0.0021 vs <1e-12 (0.0021 vs <1e-12) |
| delta 0, alpha 0.001, cap 20 | 3.7e-05 vs 0.0011 (3.7e-05 vs 0.0011) | 0.00026 vs 0.00062 (0.0071 vs 0.018) | 0.00038 vs 0.00016 (0.028 vs 0.0073) | 0.00011 vs 0.0041 (0.00011 vs 0.0041) | 0.0015 vs 0.0019 (0.0015 vs 0.0019) | 0.0018 vs <1e-12 (0.0059 vs <1e-12) | 1.8e-06 vs 5.1e-09 (1.8e-06 vs 5.1e-09) | 7.9e-05 vs 0.00091 (7.9e-05 vs 0.00091) | 0.00069 vs <1e-12 (0.00069 vs <1e-12) |
| delta 0, alpha 0.001, cap 30 | 4.6e-05 vs 0.0011 (4.6e-05 vs 0.0011) | 0.00045 vs 0.00062 (0.022 vs 0.018) | 0.00049 vs 0.00016 (0.069 vs 0.0073) | 0.00027 vs 0.0041 (0.00027 vs 0.0041) | 0.0024 vs 0.0019 (0.0024 vs 0.0019) | 0.0032 vs <1e-12 (0.014 vs <1e-12) | 2.1e-06 vs 5.1e-09 (2.1e-06 vs 5.1e-09) | 0.00015 vs 0.00091 (0.00015 vs 0.00091) | 0.001 vs <1e-12 (0.001 vs <1e-12) |
| delta 0, alpha 0.001, cap 40 | 3.4e-05 vs 0.0011 (3.4e-05 vs 0.0011) | 0.0005 vs 0.00062 (0.039 vs 0.018) | 0.00042 vs 0.00016 (0.12 vs 0.0073) | 0.00031 vs 0.0041 (0.00031 vs 0.0041) | 0.0026 vs 0.0019 (0.0026 vs 0.0019) | 0.0044 vs <1e-12 (0.026 vs <1e-12) | 1.4e-06 vs 5.1e-09 (1.4e-06 vs 5.1e-09) | 0.00015 vs 0.00091 (0.00015 vs 0.00091) | 0.0011 vs <1e-12 (0.0011 vs <1e-12) |
| delta 0, alpha 0.0001, cap 20 | 2.3e-06 vs 0.0011 (2.3e-06 vs 0.0011) | 3e-05 vs 0.00062 (0.0014 vs 0.018) | 4.1e-05 vs 0.00016 (0.013 vs 0.0073) | 3.9e-06 vs 0.0041 (3.9e-06 vs 0.0041) | 0.00023 vs 0.0019 (0.00023 vs 0.0019) | 0.00035 vs <1e-12 (0.0018 vs <1e-12) | 7.9e-08 vs 5.1e-09 (7.9e-08 vs 5.1e-09) | 5.1e-06 vs 0.00091 (5.1e-06 vs 0.00091) | 0.0001 vs <1e-12 (0.0001 vs <1e-12) |
| delta 0, alpha 0.0001, cap 30 | 2e-06 vs 0.0011 (2e-06 vs 0.0011) | 4e-05 vs 0.00062 (0.0072 vs 0.018) | 3.8e-05 vs 0.00016 (0.027 vs 0.0073) | 1.2e-05 vs 0.0041 (1.2e-05 vs 0.0041) | 0.00027 vs 0.0019 (0.00027 vs 0.0019) | 0.00041 vs <1e-12 (0.0034 vs <1e-12) | 6.6e-08 vs 5.1e-09 (6.6e-08 vs 5.1e-09) | 7e-06 vs 0.00091 (7e-06 vs 0.00091) | 0.0001 vs <1e-12 (0.0001 vs <1e-12) |
| delta 0, alpha 0.0001, cap 40 | 5.9e-07 vs 0.0011 (5.9e-07 vs 0.0011) | 4.7e-05 vs 0.00062 (0.016 vs 0.018) | 3.9e-05 vs 0.00016 (0.051 vs 0.0073) | 1.8e-05 vs 0.0041 (1.8e-05 vs 0.0041) | 0.00029 vs 0.0019 (0.00029 vs 0.0019) | 0.00053 vs <1e-12 (0.0063 vs <1e-12) | 1.1e-08 vs 5.1e-09 (1.1e-08 vs 5.1e-09) | 5.8e-06 vs 0.00091 (5.8e-06 vs 0.00091) | 0.00011 vs <1e-12 (0.00011 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 10 | 0.078 vs 0.0011 (0.078 vs 0.0011) | 0.008 vs 0.00062 (0.023 vs 0.018) | 0.0027 vs 0.00016 (0.093 vs 0.0073) | 0.0038 vs 0.0041 (0.0038 vs 0.0041) | 0.05 vs 0.0019 (0.05 vs 0.0019) | 9.3e-06 vs <1e-12 (5.4e-05 vs <1e-12) | 0.0011 vs 5.1e-09 (0.0011 vs 5.1e-09) | 0.015 vs 0.00091 (0.015 vs 0.00091) | 1e-11 vs <1e-12 (1e-11 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 20 | 0.026 vs 0.0011 (0.026 vs 0.0011) | 0.01 vs 0.00062 (0.063 vs 0.018) | 0.0012 vs 0.00016 (0.14 vs 0.0073) | 0.0087 vs 0.0041 (0.0087 vs 0.0041) | 0.04 vs 0.0019 (0.04 vs 0.0019) | 1.6e-06 vs <1e-12 (1.7e-05 vs <1e-12) | 9.9e-05 vs 5.1e-09 (9.9e-05 vs 5.1e-09) | 0.0097 vs 0.00091 (0.0097 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 30 | 0.019 vs 0.0011 (0.019 vs 0.0011) | 0.011 vs 0.00062 (0.1 vs 0.018) | 0.0011 vs 0.00016 (0.17 vs 0.0073) | 0.011 vs 0.0041 (0.011 vs 0.0041) | 0.039 vs 0.0019 (0.039 vs 0.0019) | 1.5e-06 vs <1e-12 (1.6e-05 vs <1e-12) | 4.6e-05 vs 5.1e-09 (4.6e-05 vs 5.1e-09) | 0.01 vs 0.00091 (0.01 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.05, cap 40 | 0.016 vs 0.0011 (0.016 vs 0.0011) | 0.01 vs 0.00062 (0.13 vs 0.018) | 0.00081 vs 0.00016 (0.19 vs 0.0073) | 0.01 vs 0.0041 (0.01 vs 0.0041) | 0.032 vs 0.0019 (0.032 vs 0.0019) | 1.4e-06 vs <1e-12 (1.3e-05 vs <1e-12) | 3.5e-05 vs 5.1e-09 (3.5e-05 vs 5.1e-09) | 0.0097 vs 0.00091 (0.0097 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 10 | 0.0092 vs 0.0011 (0.0092 vs 0.0011) | 0.0026 vs 0.00062 (0.015 vs 0.018) | 0.00054 vs 0.00016 (0.034 vs 0.0073) | 0.00073 vs 0.0041 (0.00073 vs 0.0041) | 0.014 vs 0.0019 (0.014 vs 0.0019) | 1.3e-06 vs <1e-12 (1e-05 vs <1e-12) | 3e-05 vs 5.1e-09 (3e-05 vs 5.1e-09) | 0.0022 vs 0.00091 (0.0022 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 20 | 0.0099 vs 0.0011 (0.0099 vs 0.0011) | 0.0033 vs 0.00062 (0.04 vs 0.018) | 0.00038 vs 0.00016 (0.087 vs 0.0073) | 0.0018 vs 0.0041 (0.0018 vs 0.0041) | 0.016 vs 0.0019 (0.016 vs 0.0019) | 2.5e-07 vs <1e-12 (4.5e-06 vs <1e-12) | 3e-05 vs 5.1e-09 (3e-05 vs 5.1e-09) | 0.0029 vs 0.00091 (0.0029 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 30 | 0.0042 vs 0.0011 (0.0042 vs 0.0011) | 0.0035 vs 0.00062 (0.066 vs 0.018) | 0.00031 vs 0.00016 (0.12 vs 0.0073) | 0.0025 vs 0.0041 (0.0025 vs 0.0041) | 0.013 vs 0.0019 (0.013 vs 0.0019) | 2.1e-07 vs <1e-12 (3.5e-06 vs <1e-12) | 3.5e-06 vs 5.1e-09 (3.5e-06 vs 5.1e-09) | 0.0022 vs 0.00091 (0.0022 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.02, cap 40 | 0.0039 vs 0.0011 (0.0039 vs 0.0011) | 0.0033 vs 0.00062 (0.094 vs 0.018) | 0.00015 vs 0.00016 (0.15 vs 0.0073) | 0.0028 vs 0.0041 (0.0028 vs 0.0041) | 0.013 vs 0.0019 (0.013 vs 0.0019) | 4.1e-08 vs <1e-12 (1.5e-06 vs <1e-12) | 3.3e-06 vs 5.1e-09 (3.3e-06 vs 5.1e-09) | 0.0024 vs 0.00091 (0.0024 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 10 | 0.0077 vs 0.0011 (0.0077 vs 0.0011) | 0.0011 vs 0.00062 (0.0039 vs 0.018) | 0.00022 vs 0.00016 (0.025 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0088 vs 0.0019 (0.0088 vs 0.0019) | 2.1e-07 vs <1e-12 (2.7e-06 vs <1e-12) | 2.8e-05 vs 5.1e-09 (2.8e-05 vs 5.1e-09) | 0.0015 vs 0.00091 (0.0015 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 20 | 0.0018 vs 0.0011 (0.0018 vs 0.0011) | 0.0015 vs 0.00062 (0.023 vs 0.018) | 0.00014 vs 0.00016 (0.07 vs 0.0073) | 0.00056 vs 0.0041 (0.00056 vs 0.0041) | 0.007 vs 0.0019 (0.007 vs 0.0019) | 4.1e-08 vs <1e-12 (1.4e-06 vs <1e-12) | 1.1e-06 vs 5.1e-09 (1.1e-06 vs 5.1e-09) | 0.00067 vs 0.00091 (0.00067 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 30 | 0.0015 vs 0.0011 (0.0015 vs 0.0011) | 0.0015 vs 0.00062 (0.051 vs 0.018) | 8.8e-05 vs 0.00016 (0.1 vs 0.0073) | 0.00088 vs 0.0041 (0.00088 vs 0.0041) | 0.0062 vs 0.0019 (0.0062 vs 0.0019) | 3.5e-08 vs <1e-12 (1e-06 vs <1e-12) | 8.6e-07 vs 5.1e-09 (8.6e-07 vs 5.1e-09) | 0.0008 vs 0.00091 (0.0008 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.01, cap 40 | 0.0014 vs 0.0011 (0.0014 vs 0.0011) | 0.0014 vs 0.00062 (0.071 vs 0.018) | 5.2e-05 vs 0.00016 (0.12 vs 0.0073) | 0.00094 vs 0.0041 (0.00094 vs 0.0041) | 0.0056 vs 0.0019 (0.0056 vs 0.0019) | 6.7e-09 vs <1e-12 (4.9e-07 vs <1e-12) | 8.3e-07 vs 5.1e-09 (8.3e-07 vs 5.1e-09) | 0.00083 vs 0.00091 (0.00083 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 10 | 0.00099 vs 0.0011 (0.00099 vs 0.0011) | 0.00053 vs 0.00062 (0.0027 vs 0.018) | 6.2e-05 vs 0.00016 (0.017 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0036 vs 0.0019 (0.0036 vs 0.0019) | 3.4e-08 vs <1e-12 (7.7e-07 vs <1e-12) | 8.8e-07 vs 5.1e-09 (8.8e-07 vs 5.1e-09) | 0.00022 vs 0.00091 (0.00022 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 20 | 0.0011 vs 0.0011 (0.0011 vs 0.0011) | 0.00065 vs 0.00062 (0.016 vs 0.018) | 4.7e-05 vs 0.00016 (0.042 vs 0.0073) | 0.00018 vs 0.0041 (0.00018 vs 0.0041) | 0.0035 vs 0.0019 (0.0035 vs 0.0019) | 6.6e-09 vs <1e-12 (4.3e-07 vs <1e-12) | 8.2e-07 vs 5.1e-09 (8.2e-07 vs 5.1e-09) | 0.00034 vs 0.00091 (0.00034 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 30 | 0.00049 vs 0.0011 (0.00049 vs 0.0011) | 0.00066 vs 0.00062 (0.035 vs 0.018) | 3.6e-05 vs 0.00016 (0.07 vs 0.0073) | 0.0003 vs 0.0041 (0.0003 vs 0.0041) | 0.0029 vs 0.0019 (0.0029 vs 0.0019) | 5.5e-09 vs <1e-12 (3.1e-07 vs <1e-12) | 1e-07 vs 5.1e-09 (1e-07 vs 5.1e-09) | 0.00026 vs 0.00091 (0.00026 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.005, cap 40 | 0.00028 vs 0.0011 (0.00028 vs 0.0011) | 0.00062 vs 0.00062 (0.056 vs 0.018) | 1.4e-05 vs 0.00016 (0.11 vs 0.0073) | 0.00029 vs 0.0041 (0.00029 vs 0.0041) | 0.0025 vs 0.0019 (0.0025 vs 0.0019) | 9.1e-10 vs <1e-12 (1.4e-07 vs <1e-12) | 3.3e-08 vs 5.1e-09 (3.3e-08 vs 5.1e-09) | 0.00021 vs 0.00091 (0.00021 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 10 | 0.00082 vs 0.0011 (0.00082 vs 0.0011) | 0.00024 vs 0.00062 (0.0017 vs 0.018) | 6.2e-05 vs 0.00016 (0.017 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0019 vs 0.0019 (0.0019 vs 0.0019) | 3.4e-08 vs <1e-12 (7.7e-07 vs <1e-12) | 7.5e-07 vs 5.1e-09 (7.5e-07 vs 5.1e-09) | 0.0002 vs 0.00091 (0.0002 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 20 | 0.00023 vs 0.0011 (0.00023 vs 0.0011) | 0.00036 vs 0.00062 (0.014 vs 0.018) | 1.1e-05 vs 0.00016 (0.03 vs 0.0073) | 0.00011 vs 0.0041 (0.00011 vs 0.0041) | 0.0018 vs 0.0019 (0.0018 vs 0.0019) | 9.1e-10 vs <1e-12 (1.1e-07 vs <1e-12) | 3.3e-08 vs 5.1e-09 (3.3e-08 vs 5.1e-09) | 0.00011 vs 0.00091 (0.00011 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 30 | 0.00017 vs 0.0011 (0.00017 vs 0.0011) | 0.00031 vs 0.00062 (0.027 vs 0.018) | 1.2e-05 vs 0.00016 (0.06 vs 0.0073) | 0.00011 vs 0.0041 (0.00011 vs 0.0041) | 0.0014 vs 0.0019 (0.0014 vs 0.0019) | 9.1e-10 vs <1e-12 (1.2e-07 vs <1e-12) | 2.3e-08 vs 5.1e-09 (2.3e-08 vs 5.1e-09) | 9.2e-05 vs 0.00091 (9.2e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.003, cap 40 | 0.00017 vs 0.0011 (0.00017 vs 0.0011) | 0.00033 vs 0.00062 (0.044 vs 0.018) | 1.1e-05 vs 0.00016 (0.084 vs 0.0073) | 0.00014 vs 0.0041 (0.00014 vs 0.0041) | 0.0014 vs 0.0019 (0.0014 vs 0.0019) | 9.1e-10 vs <1e-12 (1.1e-07 vs <1e-12) | 2.3e-08 vs 5.1e-09 (2.3e-08 vs 5.1e-09) | 0.00011 vs 0.00091 (0.00011 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 20 | 0.00015 vs 0.0011 (0.00015 vs 0.0011) | 0.00023 vs 0.00062 (0.0072 vs 0.018) | 1.1e-05 vs 0.00016 (0.03 vs 0.0073) | 2.9e-05 vs 0.0041 (2.9e-05 vs 0.0041) | 0.0013 vs 0.0019 (0.0013 vs 0.0019) | 9.1e-10 vs <1e-12 (1.1e-07 vs <1e-12) | 2.6e-08 vs 5.1e-09 (2.6e-08 vs 5.1e-09) | 5.1e-05 vs 0.00091 (5.1e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 30 | 0.00014 vs 0.0011 (0.00014 vs 0.0011) | 0.00022 vs 0.00062 (0.025 vs 0.018) | 4.8e-06 vs 0.00016 (0.05 vs 0.0073) | 6.3e-05 vs 0.0041 (6.3e-05 vs 0.0041) | 0.0011 vs 0.0019 (0.0011 vs 0.0019) | 1.4e-10 vs <1e-12 (4.2e-08 vs <1e-12) | 2.2e-08 vs 5.1e-09 (2.2e-08 vs 5.1e-09) | 6.5e-05 vs 0.00091 (6.5e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.002, cap 40 | 4.2e-05 vs 0.0011 (4.2e-05 vs 0.0011) | 0.00017 vs 0.00062 (0.036 vs 0.018) | 4.5e-06 vs 0.00016 (0.076 vs 0.0073) | 6.3e-05 vs 0.0041 (6.3e-05 vs 0.0041) | 0.00072 vs 0.0019 (0.00072 vs 0.0019) | 1.4e-10 vs <1e-12 (4e-08 vs <1e-12) | 1e-09 vs 5.1e-09 (1e-09 vs 5.1e-09) | 3.9e-05 vs 0.00091 (3.9e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 20 | 2.7e-05 vs 0.0011 (2.7e-05 vs 0.0011) | 6.7e-05 vs 0.00062 (0.0048 vs 0.018) | 3.9e-06 vs 0.00016 (0.014 vs 0.0073) | 1.4e-05 vs 0.0041 (1.4e-05 vs 0.0041) | 0.00037 vs 0.0019 (0.00037 vs 0.0019) | 1.4e-10 vs <1e-12 (3e-08 vs <1e-12) | 9.4e-10 vs 5.1e-09 (9.4e-10 vs 5.1e-09) | 1.4e-05 vs 0.00091 (1.4e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 30 | 3.1e-05 vs 0.0011 (3.1e-05 vs 0.0011) | 9.8e-05 vs 0.00062 (0.015 vs 0.018) | 3.6e-06 vs 0.00016 (0.034 vs 0.0073) | 2.7e-05 vs 0.0041 (2.7e-05 vs 0.0041) | 0.00049 vs 0.0019 (0.00049 vs 0.0019) | 1.4e-10 vs <1e-12 (3e-08 vs <1e-12) | 9.6e-10 vs 5.1e-09 (9.6e-10 vs 5.1e-09) | 2.1e-05 vs 0.00091 (2.1e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.001, cap 40 | 2.3e-05 vs 0.0011 (2.3e-05 vs 0.0011) | 9.4e-05 vs 0.00062 (0.026 vs 0.018) | 1.4e-06 vs 0.00016 (0.063 vs 0.0073) | 2.4e-05 vs 0.0041 (2.4e-05 vs 0.0041) | 0.00045 vs 0.0019 (0.00045 vs 0.0019) | 2.3e-11 vs <1e-12 (1.5e-08 vs <1e-12) | 7.3e-10 vs 5.1e-09 (7.3e-10 vs 5.1e-09) | 1.6e-05 vs 0.00091 (1.6e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.0001, cap 20 | 1.7e-06 vs 0.0011 (1.7e-06 vs 0.0011) | 7e-06 vs 0.00062 (0.00091 vs 0.018) | 1.4e-07 vs 0.00016 (0.0056 vs 0.0073) | 3.5e-07 vs 0.0041 (3.5e-07 vs 0.0041) | 4.7e-05 vs 0.0019 (4.7e-05 vs 0.0019) | <1e-12 vs <1e-12 (1.5e-09 vs <1e-12) | 1.9e-11 vs 5.1e-09 (1.9e-11 vs 5.1e-09) | 7.9e-07 vs 0.00091 (7.9e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.0001, cap 30 | 1.3e-06 vs 0.0011 (1.3e-06 vs 0.0011) | 6.5e-06 vs 0.00062 (0.0047 vs 0.018) | 6.5e-08 vs 0.00016 (0.012 vs 0.0073) | 7.2e-07 vs 0.0041 (7.2e-07 vs 0.0041) | 3.9e-05 vs 0.0019 (3.9e-05 vs 0.0019) | <1e-12 vs <1e-12 (8.3e-10 vs <1e-12) | 1.5e-11 vs 5.1e-09 (1.5e-11 vs 5.1e-09) | 8e-07 vs 0.00091 (8e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.01, alpha 0.0001, cap 40 | 3.5e-07 vs 0.0011 (3.5e-07 vs 0.0011) | 5.9e-06 vs 0.00062 (0.011 vs 0.018) | 5.3e-08 vs 0.00016 (0.023 vs 0.0073) | 7.4e-07 vs 0.0041 (7.4e-07 vs 0.0041) | 2.9e-05 vs 0.0019 (2.9e-05 vs 0.0019) | <1e-12 vs <1e-12 (8e-10 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 3.7e-07 vs 0.00091 (3.7e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 10 | 0.061 vs 0.0011 (0.061 vs 0.0011) | 0.006 vs 0.00062 (0.021 vs 0.018) | 0.00082 vs 0.00016 (0.07 vs 0.0073) | 0.0028 vs 0.0041 (0.0028 vs 0.0041) | 0.041 vs 0.0019 (0.041 vs 0.0019) | 3.8e-07 vs <1e-12 (6.7e-07 vs <1e-12) | 0.00046 vs 5.1e-09 (0.00046 vs 5.1e-09) | 0.012 vs 0.00091 (0.012 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 20 | 0.018 vs 0.0011 (0.018 vs 0.0011) | 0.0069 vs 0.00062 (0.055 vs 0.018) | 0.00028 vs 0.00016 (0.1 vs 0.0073) | 0.0059 vs 0.0041 (0.0059 vs 0.0041) | 0.028 vs 0.0019 (0.028 vs 0.0019) | 4.5e-08 vs <1e-12 (1e-07 vs <1e-12) | 4.2e-05 vs 5.1e-09 (4.2e-05 vs 5.1e-09) | 0.0057 vs 0.00091 (0.0057 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 30 | 0.013 vs 0.0011 (0.013 vs 0.0011) | 0.0069 vs 0.00062 (0.089 vs 0.018) | 0.00026 vs 0.00016 (0.12 vs 0.0073) | 0.0065 vs 0.0041 (0.0065 vs 0.0041) | 0.025 vs 0.0019 (0.025 vs 0.0019) | 4.5e-08 vs <1e-12 (9.9e-08 vs <1e-12) | 1.9e-05 vs 5.1e-09 (1.9e-05 vs 5.1e-09) | 0.0052 vs 0.00091 (0.0052 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.05, cap 40 | 0.01 vs 0.0011 (0.01 vs 0.0011) | 0.0061 vs 0.00062 (0.12 vs 0.018) | 0.00019 vs 0.00016 (0.14 vs 0.0073) | 0.006 vs 0.0041 (0.006 vs 0.0041) | 0.018 vs 0.0019 (0.018 vs 0.0019) | 4.3e-08 vs <1e-12 (9.1e-08 vs <1e-12) | 1.4e-05 vs 5.1e-09 (1.4e-05 vs 5.1e-09) | 0.0044 vs 0.00091 (0.0044 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 10 | 0.0063 vs 0.0011 (0.0063 vs 0.0011) | 0.0018 vs 0.00062 (0.013 vs 0.018) | 0.00015 vs 0.00016 (0.025 vs 0.0073) | 0.00048 vs 0.0041 (0.00048 vs 0.0041) | 0.0098 vs 0.0019 (0.0098 vs 0.0019) | 4.2e-08 vs <1e-12 (8.8e-08 vs <1e-12) | 1.2e-05 vs 5.1e-09 (1.2e-05 vs 5.1e-09) | 0.0014 vs 0.00091 (0.0014 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 20 | 0.0067 vs 0.0011 (0.0067 vs 0.0011) | 0.0021 vs 0.00062 (0.034 vs 0.018) | 7.9e-05 vs 0.00016 (0.064 vs 0.0073) | 0.0011 vs 0.0041 (0.0011 vs 0.0041) | 0.01 vs 0.0019 (0.01 vs 0.0019) | 4.2e-09 vs <1e-12 (1.3e-08 vs <1e-12) | 1.2e-05 vs 5.1e-09 (1.2e-05 vs 5.1e-09) | 0.0017 vs 0.00091 (0.0017 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 30 | 0.0025 vs 0.0011 (0.0025 vs 0.0011) | 0.0021 vs 0.00062 (0.057 vs 0.018) | 6.3e-05 vs 0.00016 (0.088 vs 0.0073) | 0.0014 vs 0.0041 (0.0014 vs 0.0041) | 0.0073 vs 0.0019 (0.0073 vs 0.0019) | 3.8e-09 vs <1e-12 (1.1e-08 vs <1e-12) | 1.3e-06 vs 5.1e-09 (1.3e-06 vs 5.1e-09) | 0.001 vs 0.00091 (0.001 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.02, cap 40 | 0.0023 vs 0.0011 (0.0023 vs 0.0011) | 0.0019 vs 0.00062 (0.08 vs 0.018) | 2.4e-05 vs 0.00016 (0.11 vs 0.0073) | 0.0015 vs 0.0041 (0.0015 vs 0.0041) | 0.0065 vs 0.0019 (0.0065 vs 0.0019) | 5e-10 vs <1e-12 (2e-09 vs <1e-12) | 1.2e-06 vs 5.1e-09 (1.2e-06 vs 5.1e-09) | 0.00099 vs 0.00091 (0.00099 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 10 | 0.0054 vs 0.0011 (0.0054 vs 0.0011) | 0.00082 vs 0.00062 (0.0035 vs 0.018) | 5.1e-05 vs 0.00016 (0.018 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0065 vs 0.0019 (0.0065 vs 0.0019) | 3.8e-09 vs <1e-12 (1.1e-08 vs <1e-12) | 1.1e-05 vs 5.1e-09 (1.1e-05 vs 5.1e-09) | 0.001 vs 0.00091 (0.001 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 20 | 0.001 vs 0.0011 (0.001 vs 0.0011) | 0.00091 vs 0.00062 (0.02 vs 0.018) | 2.4e-05 vs 0.00016 (0.051 vs 0.0073) | 0.00032 vs 0.0041 (0.00032 vs 0.0041) | 0.0041 vs 0.0019 (0.0041 vs 0.0019) | 5e-10 vs <1e-12 (2e-09 vs <1e-12) | 4.2e-07 vs 5.1e-09 (4.2e-07 vs 5.1e-09) | 0.00031 vs 0.00091 (0.00031 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 30 | 0.00086 vs 0.0011 (0.00086 vs 0.0011) | 0.00087 vs 0.00062 (0.044 vs 0.018) | 1.6e-05 vs 0.00016 (0.073 vs 0.0073) | 0.00046 vs 0.0041 (0.00046 vs 0.0041) | 0.0031 vs 0.0019 (0.0031 vs 0.0019) | 4.7e-10 vs <1e-12 (1.7e-09 vs <1e-12) | 3e-07 vs 5.1e-09 (3e-07 vs 5.1e-09) | 0.00032 vs 0.00091 (0.00032 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.01, cap 40 | 0.00079 vs 0.0011 (0.00079 vs 0.0011) | 0.00076 vs 0.00062 (0.06 vs 0.018) | 7.5e-06 vs 0.00016 (0.091 vs 0.0073) | 0.00046 vs 0.0041 (0.00046 vs 0.0041) | 0.0027 vs 0.0019 (0.0027 vs 0.0019) | 4.7e-11 vs <1e-12 (3e-10 vs <1e-12) | 2.9e-07 vs 5.1e-09 (2.9e-07 vs 5.1e-09) | 0.00031 vs 0.00091 (0.00031 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 10 | 0.00061 vs 0.0011 (0.00061 vs 0.0011) | 0.00036 vs 0.00062 (0.0024 vs 0.018) | 1.3e-05 vs 0.00016 (0.012 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0024 vs 0.0019 (0.0024 vs 0.0019) | 4.6e-10 vs <1e-12 (1.7e-09 vs <1e-12) | 3.4e-07 vs 5.1e-09 (3.4e-07 vs 5.1e-09) | 0.00012 vs 0.00091 (0.00012 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 20 | 0.00065 vs 0.0011 (0.00065 vs 0.0011) | 0.00039 vs 0.00062 (0.014 vs 0.018) | 7.1e-06 vs 0.00016 (0.031 vs 0.0073) | 0.0001 vs 0.0041 (0.0001 vs 0.0041) | 0.0019 vs 0.0019 (0.0019 vs 0.0019) | 4.7e-11 vs <1e-12 (3e-10 vs <1e-12) | 2.9e-07 vs 5.1e-09 (2.9e-07 vs 5.1e-09) | 0.00017 vs 0.00091 (0.00017 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 30 | 0.00026 vs 0.0011 (0.00026 vs 0.0011) | 0.00036 vs 0.00062 (0.029 vs 0.018) | 5.3e-06 vs 0.00016 (0.051 vs 0.0073) | 0.00015 vs 0.0041 (0.00015 vs 0.0041) | 0.0013 vs 0.0019 (0.0013 vs 0.0019) | 4.2e-11 vs <1e-12 (2.5e-10 vs <1e-12) | 3.5e-08 vs 5.1e-09 (3.5e-08 vs 5.1e-09) | 0.0001 vs 0.00091 (0.0001 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.005, cap 40 | 0.00014 vs 0.0011 (0.00014 vs 0.0011) | 0.00032 vs 0.00062 (0.047 vs 0.018) | 1.6e-06 vs 0.00016 (0.076 vs 0.0073) | 0.00013 vs 0.0041 (0.00013 vs 0.0041) | 0.0011 vs 0.0019 (0.0011 vs 0.0019) | 5.1e-12 vs <1e-12 (4.5e-11 vs <1e-12) | 1.1e-08 vs 5.1e-09 (1.1e-08 vs 5.1e-09) | 6.4e-05 vs 0.00091 (6.4e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 10 | 0.0005 vs 0.0011 (0.0005 vs 0.0011) | 0.00016 vs 0.00062 (0.0015 vs 0.018) | 1.3e-05 vs 0.00016 (0.012 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0012 vs 0.0019 (0.0012 vs 0.0019) | 4.6e-10 vs <1e-12 (1.7e-09 vs <1e-12) | 2.7e-07 vs 5.1e-09 (2.7e-07 vs 5.1e-09) | 0.00011 vs 0.00091 (0.00011 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 20 | 0.00012 vs 0.0011 (0.00012 vs 0.0011) | 0.00021 vs 0.00062 (0.012 vs 0.018) | 1.5e-06 vs 0.00016 (0.022 vs 0.0073) | 5.5e-05 vs 0.0041 (5.5e-05 vs 0.0041) | 0.00088 vs 0.0019 (0.00088 vs 0.0019) | 5.1e-12 vs <1e-12 (4.4e-11 vs <1e-12) | 1.1e-08 vs 5.1e-09 (1.1e-08 vs 5.1e-09) | 4.1e-05 vs 0.00091 (4.1e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 30 | 8.3e-05 vs 0.0011 (8.3e-05 vs 0.0011) | 0.00017 vs 0.00062 (0.022 vs 0.018) | 1.5e-06 vs 0.00016 (0.044 vs 0.0073) | 4.9e-05 vs 0.0041 (4.9e-05 vs 0.0041) | 0.00061 vs 0.0019 (0.00061 vs 0.0019) | 5.1e-12 vs <1e-12 (4.4e-11 vs <1e-12) | 7.5e-09 vs 5.1e-09 (7.5e-09 vs 5.1e-09) | 3.1e-05 vs 0.00091 (3.1e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.003, cap 40 | 8.2e-05 vs 0.0011 (8.2e-05 vs 0.0011) | 0.00016 vs 0.00062 (0.036 vs 0.018) | 1.4e-06 vs 0.00016 (0.061 vs 0.0073) | 6e-05 vs 0.0041 (6e-05 vs 0.0041) | 0.00056 vs 0.0019 (0.00056 vs 0.0019) | 5.1e-12 vs <1e-12 (4.4e-11 vs <1e-12) | 7.3e-09 vs 5.1e-09 (7.3e-09 vs 5.1e-09) | 3.4e-05 vs 0.00091 (3.4e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 20 | 7.7e-05 vs 0.0011 (7.7e-05 vs 0.0011) | 0.00014 vs 0.00062 (0.0061 vs 0.018) | 1.5e-06 vs 0.00016 (0.022 vs 0.0073) | 1.5e-05 vs 0.0041 (1.5e-05 vs 0.0041) | 0.00068 vs 0.0019 (0.00068 vs 0.0019) | 5.1e-12 vs <1e-12 (4.4e-11 vs <1e-12) | 9.1e-09 vs 5.1e-09 (9.1e-09 vs 5.1e-09) | 2.1e-05 vs 0.00091 (2.1e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 30 | 7e-05 vs 0.0011 (7e-05 vs 0.0011) | 0.00012 vs 0.00062 (0.021 vs 0.018) | 5e-07 vs 0.00016 (0.036 vs 0.0073) | 2.8e-05 vs 0.0041 (2.8e-05 vs 0.0041) | 0.00046 vs 0.0019 (0.00046 vs 0.0019) | <1e-12 vs <1e-12 (7.6e-12 vs <1e-12) | 7.2e-09 vs 5.1e-09 (7.2e-09 vs 5.1e-09) | 2.3e-05 vs 0.00091 (2.3e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.002, cap 40 | 1.8e-05 vs 0.0011 (1.8e-05 vs 0.0011) | 8e-05 vs 0.00062 (0.03 vs 0.018) | 4.7e-07 vs 0.00016 (0.055 vs 0.0073) | 2.6e-05 vs 0.0041 (2.6e-05 vs 0.0041) | 0.00026 vs 0.0019 (0.00026 vs 0.0019) | <1e-12 vs <1e-12 (7.4e-12 vs <1e-12) | 3e-10 vs 5.1e-09 (3e-10 vs 5.1e-09) | 9.9e-06 vs 0.00091 (9.9e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 20 | 1.2e-05 vs 0.0011 (1.2e-05 vs 0.0011) | 3.6e-05 vs 0.00062 (0.0041 vs 0.018) | 4.5e-07 vs 0.00016 (0.0099 vs 0.0073) | 6.5e-06 vs 0.0041 (6.5e-06 vs 0.0041) | 0.00016 vs 0.0019 (0.00016 vs 0.0019) | <1e-12 vs <1e-12 (7.3e-12 vs <1e-12) | 2.9e-10 vs 5.1e-09 (2.9e-10 vs 5.1e-09) | 4.6e-06 vs 0.00091 (4.6e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 30 | 1.4e-05 vs 0.0011 (1.4e-05 vs 0.0011) | 4.9e-05 vs 0.00062 (0.012 vs 0.018) | 4e-07 vs 0.00016 (0.025 vs 0.0073) | 1.2e-05 vs 0.0041 (1.2e-05 vs 0.0041) | 0.00019 vs 0.0019 (0.00019 vs 0.0019) | <1e-12 vs <1e-12 (7e-12 vs <1e-12) | 2.9e-10 vs 5.1e-09 (2.9e-10 vs 5.1e-09) | 6e-06 vs 0.00091 (6e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.001, cap 40 | 9.9e-06 vs 0.0011 (9.9e-06 vs 0.0011) | 4.5e-05 vs 0.00062 (0.022 vs 0.018) | 1.2e-07 vs 0.00016 (0.045 vs 0.0073) | 9.3e-06 vs 0.0041 (9.3e-06 vs 0.0041) | 0.00017 vs 0.0019 (0.00017 vs 0.0019) | <1e-12 vs <1e-12 (1.5e-12 vs <1e-12) | 2.3e-10 vs 5.1e-09 (2.3e-10 vs 5.1e-09) | 4.3e-06 vs 0.00091 (4.3e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.0001, cap 20 | 6.8e-07 vs 0.0011 (6.8e-07 vs 0.0011) | 3.6e-06 vs 0.00062 (0.00077 vs 0.018) | 1e-08 vs 0.00016 (0.004 vs 0.0073) | 1.5e-07 vs 0.0041 (1.5e-07 vs 0.0041) | 1.9e-05 vs 0.0019 (1.9e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 5.5e-12 vs 5.1e-09 (5.5e-12 vs 5.1e-09) | 2.3e-07 vs 0.00091 (2.3e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.0001, cap 30 | 5.3e-07 vs 0.0011 (5.3e-07 vs 0.0011) | 2.9e-06 vs 0.00062 (0.0039 vs 0.018) | 3.6e-09 vs 0.00016 (0.0087 vs 0.0073) | 2.6e-07 vs 0.0041 (2.6e-07 vs 0.0041) | 1.2e-05 vs 0.0019 (1.2e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 3.9e-12 vs 5.1e-09 (3.9e-12 vs 5.1e-09) | 2e-07 vs 0.00091 (2e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.015, alpha 0.0001, cap 40 | 1.1e-07 vs 0.0011 (1.1e-07 vs 0.0011) | 2.4e-06 vs 0.00062 (0.0087 vs 0.018) | 3e-09 vs 0.00016 (0.017 vs 0.0073) | 2.4e-07 vs 0.0041 (2.4e-07 vs 0.0041) | 7.8e-06 vs 0.0019 (7.8e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 6.4e-08 vs 0.00091 (6.4e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 10 | 0.051 vs 0.0011 (0.051 vs 0.0011) | 0.0044 vs 0.00062 (0.018 vs 0.018) | 0.00035 vs 0.00016 (0.054 vs 0.0073) | 0.0019 vs 0.0041 (0.0019 vs 0.0041) | 0.033 vs 0.0019 (0.033 vs 0.0019) | 1.3e-09 vs <1e-12 (1.3e-08 vs <1e-12) | 0.00024 vs 5.1e-09 (0.00024 vs 5.1e-09) | 0.0038 vs 0.00091 (0.0038 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 20 | 0.014 vs 0.0011 (0.014 vs 0.0011) | 0.004 vs 0.00062 (0.049 vs 0.018) | 0.0001 vs 0.00016 (0.079 vs 0.0073) | 0.0037 vs 0.0041 (0.0037 vs 0.0041) | 0.019 vs 0.0019 (0.019 vs 0.0019) | 9e-11 vs <1e-12 (1.3e-09 vs <1e-12) | 1.9e-05 vs 5.1e-09 (1.9e-05 vs 5.1e-09) | 0.0023 vs 0.00091 (0.0023 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 30 | 0.0094 vs 0.0011 (0.0094 vs 0.0011) | 0.0036 vs 0.00062 (0.08 vs 0.018) | 9.3e-05 vs 0.00016 (0.096 vs 0.0073) | 0.0036 vs 0.0041 (0.0036 vs 0.0041) | 0.016 vs 0.0019 (0.016 vs 0.0019) | 9e-11 vs <1e-12 (1.3e-09 vs <1e-12) | 9e-06 vs 5.1e-09 (9e-06 vs 5.1e-09) | 0.002 vs 0.00091 (0.002 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.05, cap 40 | 0.0071 vs 0.0011 (0.0071 vs 0.0011) | 0.0028 vs 0.00062 (0.1 vs 0.018) | 7.1e-05 vs 0.00016 (0.11 vs 0.0073) | 0.003 vs 0.0041 (0.003 vs 0.0041) | 0.01 vs 0.0019 (0.01 vs 0.0019) | 8.8e-11 vs <1e-12 (1.3e-09 vs <1e-12) | 6e-06 vs 5.1e-09 (6e-06 vs 5.1e-09) | 0.0016 vs 0.00091 (0.0016 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 10 | 0.0049 vs 0.0011 (0.0049 vs 0.0011) | 0.0011 vs 0.00062 (0.011 vs 0.018) | 6.1e-05 vs 0.00016 (0.019 vs 0.0073) | 0.00029 vs 0.0041 (0.00029 vs 0.0041) | 0.0065 vs 0.0019 (0.0065 vs 0.0019) | 8.8e-11 vs <1e-12 (1.3e-09 vs <1e-12) | 5.4e-06 vs 5.1e-09 (5.4e-06 vs 5.1e-09) | 0.00039 vs 0.00091 (0.00039 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 20 | 0.0051 vs 0.0011 (0.0051 vs 0.0011) | 0.0011 vs 0.00062 (0.03 vs 0.018) | 2.6e-05 vs 0.00016 (0.049 vs 0.0073) | 0.00057 vs 0.0041 (0.00057 vs 0.0041) | 0.0064 vs 0.0019 (0.0064 vs 0.0019) | 3.1e-12 vs <1e-12 (9e-11 vs <1e-12) | 5.4e-06 vs 5.1e-09 (5.4e-06 vs 5.1e-09) | 0.0005 vs 0.00091 (0.0005 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 30 | 0.0017 vs 0.0011 (0.0017 vs 0.0011) | 0.00096 vs 0.00062 (0.051 vs 0.018) | 2.1e-05 vs 0.00016 (0.068 vs 0.0073) | 0.00073 vs 0.0041 (0.00073 vs 0.0041) | 0.0039 vs 0.0019 (0.0039 vs 0.0019) | 3e-12 vs <1e-12 (8.4e-11 vs <1e-12) | 5.1e-07 vs 5.1e-09 (5.1e-07 vs 5.1e-09) | 0.00034 vs 0.00091 (0.00034 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.02, cap 40 | 0.0016 vs 0.0011 (0.0016 vs 0.0011) | 0.00082 vs 0.00062 (0.072 vs 0.018) | 6.8e-06 vs 0.00016 (0.086 vs 0.0073) | 0.00069 vs 0.0041 (0.00069 vs 0.0041) | 0.0035 vs 0.0019 (0.0035 vs 0.0019) | <1e-12 vs <1e-12 (9.6e-12 vs <1e-12) | 4.8e-07 vs 5.1e-09 (4.8e-07 vs 5.1e-09) | 0.00032 vs 0.00091 (0.00032 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 10 | 0.0042 vs 0.0011 (0.0042 vs 0.0011) | 0.00055 vs 0.00062 (0.0031 vs 0.018) | 1.8e-05 vs 0.00016 (0.014 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0045 vs 0.0019 (0.0045 vs 0.0019) | 3e-12 vs <1e-12 (8.3e-11 vs <1e-12) | 5.1e-06 vs 5.1e-09 (5.1e-06 vs 5.1e-09) | 0.00026 vs 0.00091 (0.00026 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 20 | 0.00075 vs 0.0011 (0.00075 vs 0.0011) | 0.00045 vs 0.00062 (0.018 vs 0.018) | 6.7e-06 vs 0.00016 (0.039 vs 0.0073) | 0.00017 vs 0.0041 (0.00017 vs 0.0041) | 0.0024 vs 0.0019 (0.0024 vs 0.0019) | <1e-12 vs <1e-12 (9.6e-12 vs <1e-12) | 1.9e-07 vs 5.1e-09 (1.9e-07 vs 5.1e-09) | 8.8e-05 vs 0.00091 (8.8e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 30 | 0.00059 vs 0.0011 (0.00059 vs 0.0011) | 0.00036 vs 0.00062 (0.039 vs 0.018) | 4.7e-06 vs 0.00016 (0.056 vs 0.0073) | 0.0002 vs 0.0041 (0.0002 vs 0.0041) | 0.0016 vs 0.0019 (0.0016 vs 0.0019) | <1e-12 vs <1e-12 (9.1e-12 vs <1e-12) | 1.2e-07 vs 5.1e-09 (1.2e-07 vs 5.1e-09) | 9.1e-05 vs 0.00091 (9.1e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.01, cap 40 | 0.00054 vs 0.0011 (0.00054 vs 0.0011) | 0.00029 vs 0.00062 (0.054 vs 0.018) | 1.9e-06 vs 0.00016 (0.07 vs 0.0073) | 0.00019 vs 0.0041 (0.00019 vs 0.0041) | 0.0013 vs 0.0019 (0.0013 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.2e-07 vs 5.1e-09 (1.2e-07 vs 5.1e-09) | 8.4e-05 vs 0.00091 (8.4e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 10 | 0.00048 vs 0.0011 (0.00048 vs 0.0011) | 0.00021 vs 0.00062 (0.0021 vs 0.018) | 4.1e-06 vs 0.00016 (0.0092 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0015 vs 0.0019 (0.0015 vs 0.0019) | <1e-12 vs <1e-12 (9e-12 vs <1e-12) | 1.6e-07 vs 5.1e-09 (1.6e-07 vs 5.1e-09) | 2.7e-05 vs 0.00091 (2.7e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 20 | 0.00046 vs 0.0011 (0.00046 vs 0.0011) | 0.00019 vs 0.00062 (0.012 vs 0.018) | 1.9e-06 vs 0.00016 (0.023 vs 0.0073) | 4.9e-05 vs 0.0041 (4.9e-05 vs 0.0041) | 0.001 vs 0.0019 (0.001 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.2e-07 vs 5.1e-09 (1.2e-07 vs 5.1e-09) | 4.1e-05 vs 0.00091 (4.1e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 30 | 0.00017 vs 0.0011 (0.00017 vs 0.0011) | 0.00014 vs 0.00062 (0.026 vs 0.018) | 1.4e-06 vs 0.00016 (0.039 vs 0.0073) | 6.7e-05 vs 0.0041 (6.7e-05 vs 0.0041) | 0.00062 vs 0.0019 (0.00062 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.2e-08 vs 5.1e-09 (1.2e-08 vs 5.1e-09) | 2.6e-05 vs 0.00091 (2.6e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.005, cap 40 | 8.7e-05 vs 0.0011 (8.7e-05 vs 0.0011) | 0.00011 vs 0.00062 (0.042 vs 0.018) | 3.5e-07 vs 0.00016 (0.059 vs 0.0073) | 4.8e-05 vs 0.0041 (4.8e-05 vs 0.0041) | 0.00048 vs 0.0019 (0.00048 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 4.3e-09 vs 5.1e-09 (4.3e-09 vs 5.1e-09) | 1.5e-05 vs 0.00091 (1.5e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 10 | 0.00037 vs 0.0011 (0.00037 vs 0.0011) | 9.1e-05 vs 0.00062 (0.0013 vs 0.018) | 4.1e-06 vs 0.00016 (0.0092 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0007 vs 0.0019 (0.0007 vs 0.0019) | <1e-12 vs <1e-12 (9e-12 vs <1e-12) | 1.1e-07 vs 5.1e-09 (1.1e-07 vs 5.1e-09) | 2.4e-05 vs 0.00091 (2.4e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 20 | 7.9e-05 vs 0.0011 (7.9e-05 vs 0.0011) | 8.7e-05 vs 0.00062 (0.01 vs 0.018) | 3.4e-07 vs 0.00016 (0.017 vs 0.0073) | 2.4e-05 vs 0.0041 (2.4e-05 vs 0.0041) | 0.00042 vs 0.0019 (0.00042 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 4.3e-09 vs 5.1e-09 (4.3e-09 vs 5.1e-09) | 9.9e-06 vs 0.00091 (9.9e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 30 | 5.4e-05 vs 0.0011 (5.4e-05 vs 0.0011) | 6e-05 vs 0.00062 (0.02 vs 0.018) | 3.4e-07 vs 0.00016 (0.033 vs 0.0073) | 1.9e-05 vs 0.0041 (1.9e-05 vs 0.0041) | 0.00026 vs 0.0019 (0.00026 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.7e-09 vs 5.1e-09 (2.7e-09 vs 5.1e-09) | 7e-06 vs 0.00091 (7e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.003, cap 40 | 5.2e-05 vs 0.0011 (5.2e-05 vs 0.0011) | 5.4e-05 vs 0.00062 (0.033 vs 0.018) | 3.2e-07 vs 0.00016 (0.047 vs 0.0073) | 2.2e-05 vs 0.0041 (2.2e-05 vs 0.0041) | 0.00023 vs 0.0019 (0.00023 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.7e-09 vs 5.1e-09 (2.7e-09 vs 5.1e-09) | 7.6e-06 vs 0.00091 (7.6e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 20 | 5.5e-05 vs 0.0011 (5.5e-05 vs 0.0011) | 6.2e-05 vs 0.00062 (0.0053 vs 0.018) | 3.4e-07 vs 0.00016 (0.017 vs 0.0073) | 6.6e-06 vs 0.0041 (6.6e-06 vs 0.0041) | 0.00034 vs 0.0019 (0.00034 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 3.8e-09 vs 5.1e-09 (3.8e-09 vs 5.1e-09) | 4.4e-06 vs 0.00091 (4.4e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 30 | 4.6e-05 vs 0.0011 (4.6e-05 vs 0.0011) | 4.2e-05 vs 0.00062 (0.018 vs 0.018) | 1e-07 vs 0.00016 (0.028 vs 0.0073) | 1.1e-05 vs 0.0041 (1.1e-05 vs 0.0041) | 0.0002 vs 0.0019 (0.0002 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.6e-09 vs 5.1e-09 (2.6e-09 vs 5.1e-09) | 4.9e-06 vs 0.00091 (4.9e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.002, cap 40 | 1e-05 vs 0.0011 (1e-05 vs 0.0011) | 2.4e-05 vs 0.00062 (0.027 vs 0.018) | 9.8e-08 vs 0.00016 (0.042 vs 0.0073) | 8.6e-06 vs 0.0041 (8.6e-06 vs 0.0041) | 9.3e-05 vs 0.0019 (9.3e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1e-10 vs 5.1e-09 (1e-10 vs 5.1e-09) | 2.1e-06 vs 0.00091 (2.1e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 20 | 7.6e-06 vs 0.0011 (7.6e-06 vs 0.0011) | 1.3e-05 vs 0.00062 (0.0035 vs 0.018) | 9.5e-08 vs 0.00016 (0.0073 vs 0.0073) | 2.6e-06 vs 0.0041 (2.6e-06 vs 0.0041) | 6.7e-05 vs 0.0019 (6.7e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 9.8e-11 vs 5.1e-09 (9.8e-11 vs 5.1e-09) | 9.3e-07 vs 0.00091 (9.3e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 30 | 8.4e-06 vs 0.0011 (8.4e-06 vs 0.0011) | 1.7e-05 vs 0.00062 (0.011 vs 0.018) | 8.7e-08 vs 0.00016 (0.018 vs 0.0073) | 4.3e-06 vs 0.0041 (4.3e-06 vs 0.0041) | 7.6e-05 vs 0.0019 (7.6e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 9.8e-11 vs 5.1e-09 (9.8e-11 vs 5.1e-09) | 1.2e-06 vs 0.00091 (1.2e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.001, cap 40 | 6.2e-06 vs 0.0011 (6.2e-06 vs 0.0011) | 1.5e-05 vs 0.00062 (0.019 vs 0.018) | 2.2e-08 vs 0.00016 (0.035 vs 0.0073) | 3e-06 vs 0.0041 (3e-06 vs 0.0041) | 6.7e-05 vs 0.0019 (6.7e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 8.4e-11 vs 5.1e-09 (8.4e-11 vs 5.1e-09) | 8e-07 vs 0.00091 (8e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.0001, cap 20 | 4.3e-07 vs 0.0011 (4.3e-07 vs 0.0011) | 1.3e-06 vs 0.00062 (0.00065 vs 0.018) | 1.5e-09 vs 0.00016 (0.0029 vs 0.0073) | 5.2e-08 vs 0.0041 (5.2e-08 vs 0.0041) | 7.1e-06 vs 0.0019 (7.1e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.8e-12 vs 5.1e-09 (1.8e-12 vs 5.1e-09) | 3.4e-08 vs 0.00091 (3.4e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.0001, cap 30 | 3.1e-07 vs 0.0011 (3.1e-07 vs 0.0011) | 8.2e-07 vs 0.00062 (0.0033 vs 0.018) | 4.7e-10 vs 0.00016 (0.0062 vs 0.0073) | 7.5e-08 vs 0.0041 (7.5e-08 vs 0.0041) | 4e-06 vs 0.0019 (4e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.2e-12 vs 5.1e-09 (1.2e-12 vs 5.1e-09) | 3e-08 vs 0.00091 (3e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.02, alpha 0.0001, cap 40 | 6.1e-08 vs 0.0011 (6.1e-08 vs 0.0011) | 5.4e-07 vs 0.00062 (0.0075 vs 0.018) | 4e-10 vs 0.00016 (0.012 vs 0.0073) | 5.9e-08 vs 0.0041 (5.9e-08 vs 0.0041) | 2.1e-06 vs 0.0019 (2.1e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 8.9e-09 vs 0.00091 (8.9e-09 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 10 | 0.038 vs 0.0011 (0.038 vs 0.0011) | 0.0037 vs 0.00062 (0.016 vs 0.018) | 0.00022 vs 0.00016 (0.035 vs 0.0073) | 0.0017 vs 0.0041 (0.0017 vs 0.0041) | 0.028 vs 0.0019 (0.028 vs 0.0019) | 1.4e-11 vs <1e-12 (6.8e-11 vs <1e-12) | 5.3e-05 vs 5.1e-09 (5.3e-05 vs 5.1e-09) | 0.0026 vs 0.00091 (0.0026 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 20 | 0.0097 vs 0.0011 (0.0097 vs 0.0011) | 0.0029 vs 0.00062 (0.042 vs 0.018) | 5.7e-05 vs 0.00016 (0.051 vs 0.0073) | 0.0033 vs 0.0041 (0.0033 vs 0.0041) | 0.015 vs 0.0019 (0.015 vs 0.0019) | <1e-12 vs <1e-12 (4.8e-12 vs <1e-12) | 1.1e-06 vs 5.1e-09 (1.1e-06 vs 5.1e-09) | 0.00098 vs 0.00091 (0.00098 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 30 | 0.0066 vs 0.0011 (0.0066 vs 0.0011) | 0.0024 vs 0.00062 (0.068 vs 0.018) | 5.4e-05 vs 0.00016 (0.063 vs 0.0073) | 0.003 vs 0.0041 (0.003 vs 0.0041) | 0.012 vs 0.0019 (0.012 vs 0.0019) | <1e-12 vs <1e-12 (4.8e-12 vs <1e-12) | 5.7e-07 vs 5.1e-09 (5.7e-07 vs 5.1e-09) | 0.00066 vs 0.00091 (0.00066 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.05, cap 40 | 0.0048 vs 0.0011 (0.0048 vs 0.0011) | 0.0017 vs 0.00062 (0.09 vs 0.018) | 4.2e-05 vs 0.00016 (0.073 vs 0.0073) | 0.0025 vs 0.0041 (0.0025 vs 0.0041) | 0.0074 vs 0.0019 (0.0074 vs 0.0019) | <1e-12 vs <1e-12 (4.7e-12 vs <1e-12) | 3.6e-07 vs 5.1e-09 (3.6e-07 vs 5.1e-09) | 0.00048 vs 0.00091 (0.00048 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 10 | 0.0035 vs 0.0011 (0.0035 vs 0.0011) | 0.0008 vs 0.00062 (0.0096 vs 0.018) | 3.7e-05 vs 0.00016 (0.012 vs 0.0073) | 0.00027 vs 0.0041 (0.00027 vs 0.0041) | 0.005 vs 0.0019 (0.005 vs 0.0019) | <1e-12 vs <1e-12 (4.7e-12 vs <1e-12) | 3.5e-07 vs 5.1e-09 (3.5e-07 vs 5.1e-09) | 0.00019 vs 0.00091 (0.00019 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 20 | 0.0036 vs 0.0011 (0.0036 vs 0.0011) | 0.00078 vs 0.00062 (0.025 vs 0.018) | 1.4e-05 vs 0.00016 (0.031 vs 0.0073) | 0.0005 vs 0.0041 (0.0005 vs 0.0041) | 0.0048 vs 0.0019 (0.0048 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 3.5e-07 vs 5.1e-09 (3.5e-07 vs 5.1e-09) | 0.00021 vs 0.00091 (0.00021 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 30 | 0.0011 vs 0.0011 (0.0011 vs 0.0011) | 0.00058 vs 0.00062 (0.042 vs 0.018) | 1.2e-05 vs 0.00016 (0.043 vs 0.0073) | 0.00062 vs 0.0041 (0.00062 vs 0.0041) | 0.0027 vs 0.0019 (0.0027 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 8.4e-09 vs 5.1e-09 (8.4e-09 vs 5.1e-09) | 9.6e-05 vs 0.00091 (9.6e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.02, cap 40 | 0.001 vs 0.0011 (0.001 vs 0.0011) | 0.00049 vs 0.00062 (0.06 vs 0.018) | 3.4e-06 vs 0.00016 (0.055 vs 0.0073) | 0.00057 vs 0.0041 (0.00057 vs 0.0041) | 0.0024 vs 0.0019 (0.0024 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 8.3e-09 vs 5.1e-09 (8.3e-09 vs 5.1e-09) | 8.4e-05 vs 0.00091 (8.4e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 10 | 0.003 vs 0.0011 (0.003 vs 0.0011) | 0.00043 vs 0.00062 (0.0027 vs 0.018) | 1e-05 vs 0.00016 (0.0086 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0035 vs 0.0019 (0.0035 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 3.4e-07 vs 5.1e-09 (3.4e-07 vs 5.1e-09) | 0.00015 vs 0.00091 (0.00015 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 20 | 0.00051 vs 0.0011 (0.00051 vs 0.0011) | 0.0003 vs 0.00062 (0.014 vs 0.018) | 3.4e-06 vs 0.00016 (0.024 vs 0.0073) | 0.00014 vs 0.0041 (0.00014 vs 0.0041) | 0.0017 vs 0.0019 (0.0017 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 3.7e-09 vs 5.1e-09 (3.7e-09 vs 5.1e-09) | 2.6e-05 vs 0.00091 (2.6e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 30 | 0.00038 vs 0.0011 (0.00038 vs 0.0011) | 0.00021 vs 0.00062 (0.032 vs 0.018) | 2.4e-06 vs 0.00016 (0.034 vs 0.0073) | 0.00017 vs 0.0041 (0.00017 vs 0.0041) | 0.001 vs 0.0019 (0.001 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.3e-09 vs 5.1e-09 (2.3e-09 vs 5.1e-09) | 2.2e-05 vs 0.00091 (2.2e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.01, cap 40 | 0.00035 vs 0.0011 (0.00035 vs 0.0011) | 0.00016 vs 0.00062 (0.044 vs 0.018) | 9e-07 vs 0.00016 (0.043 vs 0.0073) | 0.00015 vs 0.0041 (0.00015 vs 0.0041) | 0.00084 vs 0.0019 (0.00084 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.3e-09 vs 5.1e-09 (2.3e-09 vs 5.1e-09) | 2e-05 vs 0.00091 (2e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 10 | 0.00034 vs 0.0011 (0.00034 vs 0.0011) | 0.00016 vs 0.00062 (0.0018 vs 0.018) | 2.2e-06 vs 0.00016 (0.0055 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0012 vs 0.0019 (0.0012 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 3.6e-09 vs 5.1e-09 (3.6e-09 vs 5.1e-09) | 1.1e-05 vs 0.00091 (1.1e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 20 | 0.00031 vs 0.0011 (0.00031 vs 0.0011) | 0.00012 vs 0.00062 (0.0097 vs 0.018) | 8.9e-07 vs 0.00016 (0.014 vs 0.0073) | 4.2e-05 vs 0.0041 (4.2e-05 vs 0.0041) | 0.00072 vs 0.0019 (0.00072 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.3e-09 vs 5.1e-09 (2.3e-09 vs 5.1e-09) | 1.4e-05 vs 0.00091 (1.4e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 30 | 0.0001 vs 0.0011 (0.0001 vs 0.0011) | 7.8e-05 vs 0.00062 (0.021 vs 0.018) | 6.9e-07 vs 0.00016 (0.023 vs 0.0073) | 5.6e-05 vs 0.0041 (5.6e-05 vs 0.0041) | 0.0004 vs 0.0019 (0.0004 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 6.3e-11 vs 5.1e-09 (6.3e-11 vs 5.1e-09) | 5.9e-06 vs 0.00091 (5.9e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.005, cap 40 | 5.4e-05 vs 0.0011 (5.4e-05 vs 0.0011) | 6e-05 vs 0.00062 (0.033 vs 0.018) | 1.6e-07 vs 0.00016 (0.035 vs 0.0073) | 3.8e-05 vs 0.0041 (3.8e-05 vs 0.0041) | 0.0003 vs 0.0019 (0.0003 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.4e-11 vs 5.1e-09 (2.4e-11 vs 5.1e-09) | 2.6e-06 vs 0.00091 (2.6e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 10 | 0.00025 vs 0.0011 (0.00025 vs 0.0011) | 6.4e-05 vs 0.00062 (0.0011 vs 0.018) | 2.2e-06 vs 0.00016 (0.0055 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0005 vs 0.0019 (0.0005 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.2e-09 vs 5.1e-09 (2.2e-09 vs 5.1e-09) | 9.9e-06 vs 0.00091 (9.9e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 20 | 5e-05 vs 0.0011 (5e-05 vs 0.0011) | 5e-05 vs 0.00062 (0.0083 vs 0.018) | 1.5e-07 vs 0.00016 (0.0096 vs 0.0073) | 2e-05 vs 0.0041 (2e-05 vs 0.0041) | 0.00027 vs 0.0019 (0.00027 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.4e-11 vs 5.1e-09 (2.4e-11 vs 5.1e-09) | 2.1e-06 vs 0.00091 (2.1e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 30 | 3.3e-05 vs 0.0011 (3.3e-05 vs 0.0011) | 3.1e-05 vs 0.00062 (0.016 vs 0.018) | 1.5e-07 vs 0.00016 (0.019 vs 0.0073) | 1.5e-05 vs 0.0041 (1.5e-05 vs 0.0041) | 0.00016 vs 0.0019 (0.00016 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.5e-11 vs 5.1e-09 (1.5e-11 vs 5.1e-09) | 1.4e-06 vs 0.00091 (1.4e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.003, cap 40 | 3.2e-05 vs 0.0011 (3.2e-05 vs 0.0011) | 2.6e-05 vs 0.00062 (0.026 vs 0.018) | 1.5e-07 vs 0.00016 (0.027 vs 0.0073) | 1.7e-05 vs 0.0041 (1.7e-05 vs 0.0041) | 0.00014 vs 0.0019 (0.00014 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.5e-11 vs 5.1e-09 (1.5e-11 vs 5.1e-09) | 1.4e-06 vs 0.00091 (1.4e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 20 | 3.7e-05 vs 0.0011 (3.7e-05 vs 0.0011) | 3.8e-05 vs 0.00062 (0.0043 vs 0.018) | 1.5e-07 vs 0.00016 (0.0096 vs 0.0073) | 5.7e-06 vs 0.0041 (5.7e-06 vs 0.0041) | 0.00023 vs 0.0019 (0.00023 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.4e-11 vs 5.1e-09 (2.4e-11 vs 5.1e-09) | 1.1e-06 vs 0.00091 (1.1e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 30 | 2.9e-05 vs 0.0011 (2.9e-05 vs 0.0011) | 2.2e-05 vs 0.00062 (0.014 vs 0.018) | 4.3e-08 vs 0.00016 (0.016 vs 0.0073) | 8.7e-06 vs 0.0041 (8.7e-06 vs 0.0041) | 0.00012 vs 0.0019 (0.00012 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.5e-11 vs 5.1e-09 (1.5e-11 vs 5.1e-09) | 1.1e-06 vs 0.00091 (1.1e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.002, cap 40 | 5.8e-06 vs 0.0011 (5.8e-06 vs 0.0011) | 1.1e-05 vs 0.00062 (0.021 vs 0.018) | 4.2e-08 vs 0.00016 (0.024 vs 0.0073) | 6.6e-06 vs 0.0041 (6.6e-06 vs 0.0041) | 5.2e-05 vs 0.0019 (5.2e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 2.5e-07 vs 0.00091 (2.5e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 20 | 4.5e-06 vs 0.0011 (4.5e-06 vs 0.0011) | 7.1e-06 vs 0.00062 (0.0028 vs 0.018) | 4.1e-08 vs 0.00016 (0.0042 vs 0.0073) | 2.1e-06 vs 0.0041 (2.1e-06 vs 0.0041) | 4e-05 vs 0.0019 (4e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.6e-07 vs 0.00091 (1.6e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 30 | 5e-06 vs 0.0011 (5e-06 vs 0.0011) | 8.3e-06 vs 0.00062 (0.0084 vs 0.018) | 3.8e-08 vs 0.00016 (0.01 vs 0.0073) | 3.4e-06 vs 0.0041 (3.4e-06 vs 0.0041) | 4.4e-05 vs 0.0019 (4.4e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.8e-07 vs 0.00091 (1.8e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.001, cap 40 | 3.7e-06 vs 0.0011 (3.7e-06 vs 0.0011) | 7.2e-06 vs 0.00062 (0.015 vs 0.018) | 8.9e-09 vs 0.00016 (0.019 vs 0.0073) | 2.3e-06 vs 0.0041 (2.3e-06 vs 0.0041) | 3.9e-05 vs 0.0019 (3.9e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.1e-07 vs 0.00091 (1.1e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.0001, cap 20 | 2.5e-07 vs 0.0011 (2.5e-07 vs 0.0011) | 6.4e-07 vs 0.00062 (0.00051 vs 0.018) | 5.2e-10 vs 0.00016 (0.0016 vs 0.0073) | 4.2e-08 vs 0.0041 (4.2e-08 vs 0.0041) | 4e-06 vs 0.0019 (4e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 5.1e-09 vs 0.00091 (5.1e-09 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.0001, cap 30 | 1.8e-07 vs 0.0011 (1.8e-07 vs 0.0011) | 3.5e-07 vs 0.00062 (0.0025 vs 0.018) | 1.5e-10 vs 0.00016 (0.0033 vs 0.0073) | 5.7e-08 vs 0.0041 (5.7e-08 vs 0.0041) | 2.1e-06 vs 0.0019 (2.1e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 4e-09 vs 0.00091 (4e-09 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.025, alpha 0.0001, cap 40 | 3.2e-08 vs 0.0011 (3.2e-08 vs 0.0011) | 2e-07 vs 0.00062 (0.0057 vs 0.018) | 1.3e-10 vs 0.00016 (0.0065 vs 0.0073) | 4.3e-08 vs 0.0041 (4.3e-08 vs 0.0041) | 9.9e-07 vs 0.0019 (9.9e-07 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 6.5e-10 vs 0.00091 (6.5e-10 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 10 | 0.028 vs 0.0011 (0.028 vs 0.0011) | 0.003 vs 0.00062 (0.014 vs 0.018) | 0.00014 vs 0.00016 (0.023 vs 0.0073) | 0.0017 vs 0.0041 (0.0017 vs 0.0041) | 0.023 vs 0.0019 (0.023 vs 0.0019) | 1.3e-12 vs <1e-12 (1.2e-12 vs <1e-12) | 3.7e-08 vs 5.1e-09 (3.7e-08 vs 5.1e-09) | 0.002 vs 0.00091 (0.002 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 20 | 0.0061 vs 0.0011 (0.0061 vs 0.0011) | 0.002 vs 0.00062 (0.035 vs 0.018) | 3.2e-05 vs 0.00016 (0.034 vs 0.0073) | 0.0033 vs 0.0041 (0.0033 vs 0.0041) | 0.011 vs 0.0019 (0.011 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 3.8e-08 vs 5.1e-09 (3.8e-08 vs 5.1e-09) | 0.00055 vs 0.00091 (0.00055 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 30 | 0.004 vs 0.0011 (0.004 vs 0.0011) | 0.0016 vs 0.00062 (0.056 vs 0.018) | 3.1e-05 vs 0.00016 (0.041 vs 0.0073) | 0.003 vs 0.0041 (0.003 vs 0.0041) | 0.0092 vs 0.0019 (0.0092 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.5e-09 vs 5.1e-09 (1.5e-09 vs 5.1e-09) | 0.00032 vs 0.00091 (0.00032 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.05, cap 40 | 0.0028 vs 0.0011 (0.0028 vs 0.0011) | 0.00094 vs 0.00062 (0.073 vs 0.018) | 2.4e-05 vs 0.00016 (0.047 vs 0.0073) | 0.0025 vs 0.0041 (0.0025 vs 0.0041) | 0.0051 vs 0.0019 (0.0051 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 8.8e-10 vs 5.1e-09 (8.8e-10 vs 5.1e-09) | 0.00022 vs 0.00091 (0.00022 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 10 | 0.0022 vs 0.0011 (0.0022 vs 0.0011) | 0.00055 vs 0.00062 (0.008 vs 0.018) | 2.2e-05 vs 0.00016 (0.008 vs 0.0073) | 0.00027 vs 0.0041 (0.00027 vs 0.0041) | 0.0037 vs 0.0019 (0.0037 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 3.8e-10 vs 5.1e-09 (3.8e-10 vs 5.1e-09) | 0.00011 vs 0.00091 (0.00011 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 20 | 0.0022 vs 0.0011 (0.0022 vs 0.0011) | 0.0005 vs 0.00062 (0.02 vs 0.018) | 7.6e-06 vs 0.00016 (0.02 vs 0.0073) | 0.0005 vs 0.0041 (0.0005 vs 0.0041) | 0.0034 vs 0.0019 (0.0034 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.2e-10 vs 5.1e-09 (2.2e-10 vs 5.1e-09) | 0.00012 vs 0.00091 (0.00012 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 30 | 0.0006 vs 0.0011 (0.0006 vs 0.0011) | 0.00032 vs 0.00062 (0.034 vs 0.018) | 6.3e-06 vs 0.00016 (0.028 vs 0.0073) | 0.00062 vs 0.0041 (0.00062 vs 0.0041) | 0.0018 vs 0.0019 (0.0018 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.2e-10 vs 5.1e-09 (2.2e-10 vs 5.1e-09) | 4.2e-05 vs 0.00091 (4.2e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.02, cap 40 | 0.00055 vs 0.0011 (0.00055 vs 0.0011) | 0.00027 vs 0.00062 (0.048 vs 0.018) | 1.7e-06 vs 0.00016 (0.036 vs 0.0073) | 0.00057 vs 0.0041 (0.00057 vs 0.0041) | 0.0016 vs 0.0019 (0.0016 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.1e-10 vs 5.1e-09 (2.1e-10 vs 5.1e-09) | 3.6e-05 vs 0.00091 (3.6e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 10 | 0.0019 vs 0.0011 (0.0019 vs 0.0011) | 0.00032 vs 0.00062 (0.0023 vs 0.018) | 5.7e-06 vs 0.00016 (0.0057 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0026 vs 0.0019 (0.0026 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 9.5e-05 vs 0.00091 (9.5e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 20 | 0.00028 vs 0.0011 (0.00028 vs 0.0011) | 0.00018 vs 0.00062 (0.012 vs 0.018) | 1.7e-06 vs 0.00016 (0.016 vs 0.0073) | 0.00014 vs 0.0041 (0.00014 vs 0.0041) | 0.0012 vs 0.0019 (0.0012 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 5.6e-12 vs 5.1e-09 (5.6e-12 vs 5.1e-09) | 1.2e-05 vs 0.00091 (1.2e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 30 | 0.0002 vs 0.0011 (0.0002 vs 0.0011) | 0.00011 vs 0.00062 (0.025 vs 0.018) | 1.3e-06 vs 0.00016 (0.022 vs 0.0073) | 0.00017 vs 0.0041 (0.00017 vs 0.0041) | 0.00064 vs 0.0019 (0.00064 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.3e-12 vs 5.1e-09 (2.3e-12 vs 5.1e-09) | 9.2e-06 vs 0.00091 (9.2e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.01, cap 40 | 0.00018 vs 0.0011 (0.00018 vs 0.0011) | 7.9e-05 vs 0.00062 (0.035 vs 0.018) | 4.2e-07 vs 0.00016 (0.028 vs 0.0073) | 0.00015 vs 0.0041 (0.00015 vs 0.0041) | 0.00052 vs 0.0019 (0.00052 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.3e-12 vs 5.1e-09 (1.3e-12 vs 5.1e-09) | 8.2e-06 vs 0.00091 (8.2e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 10 | 0.0002 vs 0.0011 (0.0002 vs 0.0011) | 0.00011 vs 0.00062 (0.0015 vs 0.018) | 1.1e-06 vs 0.00016 (0.0036 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.00085 vs 0.0019 (0.00085 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 6e-06 vs 0.00091 (6e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 20 | 0.00017 vs 0.0011 (0.00017 vs 0.0011) | 6.5e-05 vs 0.00062 (0.0077 vs 0.018) | 4.2e-07 vs 0.00016 (0.0089 vs 0.0073) | 4.2e-05 vs 0.0041 (4.2e-05 vs 0.0041) | 0.00046 vs 0.0019 (0.00046 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.3e-12 vs 5.1e-09 (1.3e-12 vs 5.1e-09) | 6.7e-06 vs 0.00091 (6.7e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 30 | 4.8e-05 vs 0.0011 (4.8e-05 vs 0.0011) | 3.7e-05 vs 0.00062 (0.016 vs 0.018) | 3.3e-07 vs 0.00016 (0.015 vs 0.0073) | 5.6e-05 vs 0.0041 (5.6e-05 vs 0.0041) | 0.00024 vs 0.0019 (0.00024 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.2e-12 vs 5.1e-09 (1.2e-12 vs 5.1e-09) | 2.2e-06 vs 0.00091 (2.2e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.005, cap 40 | 2.4e-05 vs 0.0011 (2.4e-05 vs 0.0011) | 2.8e-05 vs 0.00062 (0.026 vs 0.018) | 7e-08 vs 0.00016 (0.023 vs 0.0073) | 3.8e-05 vs 0.0041 (3.8e-05 vs 0.0041) | 0.00018 vs 0.0019 (0.00018 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 8.4e-07 vs 0.00091 (8.4e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 10 | 0.00014 vs 0.0011 (0.00014 vs 0.0011) | 4.1e-05 vs 0.00062 (0.00092 vs 0.018) | 1.1e-06 vs 0.00016 (0.0036 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.00034 vs 0.0019 (0.00034 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 5.2e-06 vs 0.00091 (5.2e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 20 | 2.3e-05 vs 0.0011 (2.3e-05 vs 0.0011) | 2.5e-05 vs 0.00062 (0.0066 vs 0.018) | 6.9e-08 vs 0.00016 (0.0062 vs 0.0073) | 2e-05 vs 0.0041 (2e-05 vs 0.0041) | 0.00017 vs 0.0019 (0.00017 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 7.5e-07 vs 0.00091 (7.5e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 30 | 1.5e-05 vs 0.0011 (1.5e-05 vs 0.0011) | 1.4e-05 vs 0.00062 (0.012 vs 0.018) | 6.9e-08 vs 0.00016 (0.013 vs 0.0073) | 1.5e-05 vs 0.0041 (1.5e-05 vs 0.0041) | 9e-05 vs 0.0019 (9e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 4.7e-07 vs 0.00091 (4.7e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.003, cap 40 | 1.4e-05 vs 0.0011 (1.4e-05 vs 0.0011) | 1.1e-05 vs 0.00062 (0.02 vs 0.018) | 6.7e-08 vs 0.00016 (0.018 vs 0.0073) | 1.7e-05 vs 0.0041 (1.7e-05 vs 0.0041) | 7.4e-05 vs 0.0019 (7.4e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 4.7e-07 vs 0.00091 (4.7e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 20 | 1.8e-05 vs 0.0011 (1.8e-05 vs 0.0011) | 2e-05 vs 0.00062 (0.0034 vs 0.018) | 6.9e-08 vs 0.00016 (0.0062 vs 0.0073) | 5.7e-06 vs 0.0041 (5.7e-06 vs 0.0041) | 0.00014 vs 0.0019 (0.00014 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 4.4e-07 vs 0.00091 (4.4e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 30 | 1.3e-05 vs 0.0011 (1.3e-05 vs 0.0011) | 9.7e-06 vs 0.00062 (0.011 vs 0.018) | 1.8e-08 vs 0.00016 (0.01 vs 0.0073) | 8.7e-06 vs 0.0041 (8.7e-06 vs 0.0041) | 6.7e-05 vs 0.0019 (6.7e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 4e-07 vs 0.00091 (4e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.002, cap 40 | 2.2e-06 vs 0.0011 (2.2e-06 vs 0.0011) | 4.2e-06 vs 0.00062 (0.016 vs 0.018) | 1.7e-08 vs 0.00016 (0.016 vs 0.0073) | 6.6e-06 vs 0.0041 (6.6e-06 vs 0.0041) | 2.7e-05 vs 0.0019 (2.7e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 6.3e-08 vs 0.00091 (6.3e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 20 | 1.8e-06 vs 0.0011 (1.8e-06 vs 0.0011) | 3.2e-06 vs 0.00062 (0.0022 vs 0.018) | 1.7e-08 vs 0.00016 (0.0027 vs 0.0073) | 2.1e-06 vs 0.0041 (2.1e-06 vs 0.0041) | 2.2e-05 vs 0.0019 (2.2e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 4.4e-08 vs 0.00091 (4.4e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 30 | 1.9e-06 vs 0.0011 (1.9e-06 vs 0.0011) | 3.5e-06 vs 0.00062 (0.0065 vs 0.018) | 1.6e-08 vs 0.00016 (0.0067 vs 0.0073) | 3.4e-06 vs 0.0041 (3.4e-06 vs 0.0041) | 2.4e-05 vs 0.0019 (2.4e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 5e-08 vs 0.00091 (5e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.001, cap 40 | 1.5e-06 vs 0.0011 (1.5e-06 vs 0.0011) | 3e-06 vs 0.00062 (0.012 vs 0.018) | 3.6e-09 vs 0.00016 (0.013 vs 0.0073) | 2.3e-06 vs 0.0041 (2.3e-06 vs 0.0041) | 2.1e-05 vs 0.0019 (2.1e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 3.1e-08 vs 0.00091 (3.1e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.0001, cap 20 | 9.6e-08 vs 0.0011 (9.6e-08 vs 0.0011) | 2.7e-07 vs 0.00062 (0.0004 vs 0.018) | 1.8e-10 vs 0.00016 (0.00099 vs 0.0073) | 4.2e-08 vs 0.0041 (4.2e-08 vs 0.0041) | 2.1e-06 vs 0.0019 (2.1e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.3e-09 vs 0.00091 (1.3e-09 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.0001, cap 30 | 6.2e-08 vs 0.0011 (6.2e-08 vs 0.0011) | 1.2e-07 vs 0.00062 (0.002 vs 0.018) | 4.9e-11 vs 0.00016 (0.0021 vs 0.0073) | 5.7e-08 vs 0.0041 (5.7e-08 vs 0.0041) | 9.4e-07 vs 0.0019 (9.4e-07 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1e-09 vs 0.00091 (1e-09 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.03, alpha 0.0001, cap 40 | 9.6e-09 vs 0.0011 (9.6e-09 vs 0.0011) | 6e-08 vs 0.00062 (0.0044 vs 0.018) | 4.4e-11 vs 0.00016 (0.0042 vs 0.0073) | 4.3e-08 vs 0.0041 (4.3e-08 vs 0.0041) | 4.2e-07 vs 0.0019 (4.2e-07 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.1e-10 vs 0.00091 (1.1e-10 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 10 | 0.012 vs 0.0011 (0.012 vs 0.0011) | 0.0018 vs 0.00062 (0.0098 vs 0.018) | 6.9e-05 vs 0.00016 (0.0091 vs 0.0073) | 0.00038 vs 0.0041 (0.00038 vs 0.0041) | 0.014 vs 0.0019 (0.014 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.6e-09 vs 5.1e-09 (1.6e-09 vs 5.1e-09) | 0.0015 vs 0.00091 (0.0015 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 20 | 0.0018 vs 0.0011 (0.0018 vs 0.0011) | 0.0011 vs 0.00062 (0.024 vs 0.018) | 1.5e-05 vs 0.00016 (0.013 vs 0.0073) | 0.00059 vs 0.0041 (0.00059 vs 0.0041) | 0.005 vs 0.0019 (0.005 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.7e-09 vs 5.1e-09 (1.7e-09 vs 5.1e-09) | 0.0003 vs 0.00091 (0.0003 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 30 | 0.0012 vs 0.0011 (0.0012 vs 0.0011) | 0.00082 vs 0.00062 (0.038 vs 0.018) | 1.5e-05 vs 0.00016 (0.015 vs 0.0073) | 0.00032 vs 0.0041 (0.00032 vs 0.0041) | 0.0041 vs 0.0019 (0.0041 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 3.2e-11 vs 5.1e-09 (3.2e-11 vs 5.1e-09) | 0.00015 vs 0.00091 (0.00015 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.05, cap 40 | 0.00072 vs 0.0011 (0.00072 vs 0.0011) | 0.00047 vs 0.00062 (0.05 vs 0.018) | 1.2e-05 vs 0.00016 (0.018 vs 0.0073) | 0.00021 vs 0.0041 (0.00021 vs 0.0041) | 0.0018 vs 0.0019 (0.0018 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 2.5e-11 vs 5.1e-09 (2.5e-11 vs 5.1e-09) | 0.0001 vs 0.00091 (0.0001 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 10 | 0.00065 vs 0.0011 (0.00065 vs 0.0011) | 0.00029 vs 0.00062 (0.0055 vs 0.018) | 1.1e-05 vs 0.00016 (0.003 vs 0.0073) | 4e-05 vs 0.0041 (4e-05 vs 0.0041) | 0.0016 vs 0.0019 (0.0016 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.7e-11 vs 5.1e-09 (1.7e-11 vs 5.1e-09) | 7e-05 vs 0.00091 (7e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 20 | 0.00063 vs 0.0011 (0.00063 vs 0.0011) | 0.00026 vs 0.00062 (0.014 vs 0.018) | 3.2e-06 vs 0.00016 (0.0073 vs 0.0073) | 5.1e-05 vs 0.0041 (5.1e-05 vs 0.0041) | 0.0014 vs 0.0019 (0.0014 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 5.8e-12 vs 5.1e-09 (5.8e-12 vs 5.1e-09) | 7.1e-05 vs 0.00091 (7.1e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 30 | 0.00012 vs 0.0011 (0.00012 vs 0.0011) | 0.00015 vs 0.00062 (0.023 vs 0.018) | 2.7e-06 vs 0.00016 (0.01 vs 0.0073) | 5.6e-05 vs 0.0041 (5.6e-05 vs 0.0041) | 0.00053 vs 0.0019 (0.00053 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 5.8e-12 vs 5.1e-09 (5.8e-12 vs 5.1e-09) | 1.7e-05 vs 0.00091 (1.7e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.02, cap 40 | 0.00011 vs 0.0011 (0.00011 vs 0.0011) | 0.00013 vs 0.00062 (0.033 vs 0.018) | 6.8e-07 vs 0.00016 (0.013 vs 0.0073) | 4.4e-05 vs 0.0041 (4.4e-05 vs 0.0041) | 0.00049 vs 0.0019 (0.00049 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 5.7e-12 vs 5.1e-09 (5.7e-12 vs 5.1e-09) | 1.5e-05 vs 0.00091 (1.5e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 10 | 0.00058 vs 0.0011 (0.00058 vs 0.0011) | 0.00017 vs 0.00062 (0.0016 vs 0.018) | 2.5e-06 vs 0.00016 (0.0021 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.0012 vs 0.0019 (0.0012 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 6e-05 vs 0.00091 (6e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 20 | 6.3e-05 vs 0.0011 (6.3e-05 vs 0.0011) | 8.5e-05 vs 0.00062 (0.0079 vs 0.018) | 6.7e-07 vs 0.00016 (0.0055 vs 0.0073) | 1.1e-05 vs 0.0041 (1.1e-05 vs 0.0041) | 0.00038 vs 0.0019 (0.00038 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 5.1e-06 vs 0.00091 (5.1e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 30 | 3.6e-05 vs 0.0011 (3.6e-05 vs 0.0011) | 4.7e-05 vs 0.00062 (0.017 vs 0.018) | 5.2e-07 vs 0.00016 (0.0077 vs 0.0073) | 8.6e-06 vs 0.0041 (8.6e-06 vs 0.0041) | 0.00016 vs 0.0019 (0.00016 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 3.8e-06 vs 0.00091 (3.8e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.01, cap 40 | 3.4e-05 vs 0.0011 (3.4e-05 vs 0.0011) | 3.5e-05 vs 0.00062 (0.024 vs 0.018) | 1.5e-07 vs 0.00016 (0.0098 vs 0.0073) | 5.9e-06 vs 0.0041 (5.9e-06 vs 0.0041) | 0.00013 vs 0.0019 (0.00013 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 3.4e-06 vs 0.00091 (3.4e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 10 | 5.3e-05 vs 0.0011 (5.3e-05 vs 0.0011) | 5.5e-05 vs 0.00062 (0.001 vs 0.018) | 4.8e-07 vs 0.00016 (0.0013 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.00031 vs 0.0019 (0.00031 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 3.2e-06 vs 0.00091 (3.2e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 20 | 3.3e-05 vs 0.0011 (3.3e-05 vs 0.0011) | 3e-05 vs 0.00062 (0.0052 vs 0.018) | 1.5e-07 vs 0.00016 (0.0031 vs 0.0073) | 2.9e-06 vs 0.0041 (2.9e-06 vs 0.0041) | 0.00013 vs 0.0019 (0.00013 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 3.1e-06 vs 0.00091 (3.1e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 30 | 6.6e-06 vs 0.0011 (6.6e-06 vs 0.0011) | 1.6e-05 vs 0.00062 (0.011 vs 0.018) | 1.2e-07 vs 0.00016 (0.0051 vs 0.0073) | 3.1e-06 vs 0.0041 (3.1e-06 vs 0.0041) | 4.9e-05 vs 0.0019 (4.9e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 7.5e-07 vs 0.00091 (7.5e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.005, cap 40 | 3.5e-06 vs 0.0011 (3.5e-06 vs 0.0011) | 1.1e-05 vs 0.00062 (0.018 vs 0.018) | 2.4e-08 vs 0.00016 (0.0078 vs 0.0073) | 1.2e-06 vs 0.0041 (1.2e-06 vs 0.0041) | 3.6e-05 vs 0.0019 (3.6e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 2.7e-07 vs 0.00091 (2.7e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 10 | 3e-05 vs 0.0011 (3e-05 vs 0.0011) | 2e-05 vs 0.00062 (0.00063 vs 0.018) | 4.8e-07 vs 0.00016 (0.0013 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.00011 vs 0.0019 (0.00011 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 2.6e-06 vs 0.00091 (2.6e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 20 | 3.4e-06 vs 0.0011 (3.4e-06 vs 0.0011) | 1.1e-05 vs 0.00062 (0.0044 vs 0.018) | 2.4e-08 vs 0.00016 (0.0021 vs 0.0073) | 9.6e-07 vs 0.0041 (9.6e-07 vs 0.0041) | 3.6e-05 vs 0.0019 (3.6e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 2.5e-07 vs 0.00091 (2.5e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 30 | 1.9e-06 vs 0.0011 (1.9e-06 vs 0.0011) | 5.6e-06 vs 0.00062 (0.0082 vs 0.018) | 2.4e-08 vs 0.00016 (0.0043 vs 0.0073) | 5e-07 vs 0.0041 (5e-07 vs 0.0041) | 1.6e-05 vs 0.0019 (1.6e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.6e-07 vs 0.00091 (1.6e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.003, cap 40 | 1.8e-06 vs 0.0011 (1.8e-06 vs 0.0011) | 4.4e-06 vs 0.00062 (0.013 vs 0.018) | 2.3e-08 vs 0.00016 (0.006 vs 0.0073) | 4.5e-07 vs 0.0041 (4.5e-07 vs 0.0041) | 1.3e-05 vs 0.0019 (1.3e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.6e-07 vs 0.00091 (1.6e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 20 | 3.1e-06 vs 0.0011 (3.1e-06 vs 0.0011) | 8.8e-06 vs 0.00062 (0.0023 vs 0.018) | 2.4e-08 vs 0.00016 (0.0021 vs 0.0073) | 2.8e-07 vs 0.0041 (2.8e-07 vs 0.0041) | 3.3e-05 vs 0.0019 (3.3e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.7e-07 vs 0.00091 (1.7e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 30 | 1.8e-06 vs 0.0011 (1.8e-06 vs 0.0011) | 3.9e-06 vs 0.00062 (0.0074 vs 0.018) | 5.4e-09 vs 0.00016 (0.0034 vs 0.0073) | 2.7e-07 vs 0.0041 (2.7e-07 vs 0.0041) | 1.2e-05 vs 0.0019 (1.2e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.4e-07 vs 0.00091 (1.4e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.002, cap 40 | 1.9e-07 vs 0.0011 (1.9e-07 vs 0.0011) | 1.5e-06 vs 0.00062 (0.011 vs 0.018) | 5.2e-09 vs 0.00016 (0.0053 vs 0.0073) | 1.3e-07 vs 0.0041 (1.3e-07 vs 0.0041) | 3.5e-06 vs 0.0019 (3.5e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.5e-08 vs 0.00091 (1.5e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 20 | 1.9e-07 vs 0.0011 (1.9e-07 vs 0.0011) | 1.2e-06 vs 0.00062 (0.0014 vs 0.018) | 5.2e-09 vs 0.00016 (0.0009 vs 0.0073) | 6.7e-08 vs 0.0041 (6.7e-08 vs 0.0041) | 3.3e-06 vs 0.0019 (3.3e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.2e-08 vs 0.00091 (1.2e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 30 | 1.9e-07 vs 0.0011 (1.9e-07 vs 0.0011) | 1.3e-06 vs 0.00062 (0.0043 vs 0.018) | 4.9e-09 vs 0.00016 (0.0022 vs 0.0073) | 8.6e-08 vs 0.0041 (8.6e-08 vs 0.0041) | 3.4e-06 vs 0.0019 (3.4e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.3e-08 vs 0.00091 (1.3e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.001, cap 40 | 1.6e-07 vs 0.0011 (1.6e-07 vs 0.0011) | 1.1e-06 vs 0.00062 (0.0075 vs 0.018) | 1e-09 vs 0.00016 (0.0042 vs 0.0073) | 4e-08 vs 0.0041 (4e-08 vs 0.0041) | 3.1e-06 vs 0.0019 (3.1e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 8.6e-09 vs 0.00091 (8.6e-09 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.0001, cap 20 | 7.8e-09 vs 0.0011 (7.8e-09 vs 0.0011) | 9.3e-08 vs 0.00062 (0.00025 vs 0.018) | 4.5e-11 vs 0.00016 (0.00032 vs 0.0073) | 8.2e-10 vs 0.0041 (8.2e-10 vs 0.0041) | 2.4e-07 vs 0.0019 (2.4e-07 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 3.3e-10 vs 0.00091 (3.3e-10 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.0001, cap 30 | 4.2e-09 vs 0.0011 (4.2e-09 vs 0.0011) | 4e-08 vs 0.00062 (0.0012 vs 0.018) | 1e-11 vs 0.00016 (0.00068 vs 0.0073) | 5.6e-10 vs 0.0041 (5.6e-10 vs 0.0041) | 8.7e-08 vs 0.0019 (8.7e-08 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 2.4e-10 vs 0.00091 (2.4e-10 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.04, alpha 0.0001, cap 40 | 4.7e-10 vs 0.0011 (4.7e-10 vs 0.0011) | 1.8e-08 vs 0.00062 (0.0027 vs 0.018) | 9.4e-12 vs 0.00016 (0.0014 vs 0.0073) | 2.8e-10 vs 0.0041 (2.8e-10 vs 0.0041) | 2.7e-08 vs 0.0019 (2.7e-08 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.9e-11 vs 0.00091 (1.9e-11 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 10 | 0.0037 vs 0.0011 (0.0037 vs 0.0011) | 0.00075 vs 0.00062 (0.0075 vs 0.018) | 4.6e-05 vs 0.00016 (0.0034 vs 0.0073) | 0.00026 vs 0.0041 (0.00026 vs 0.0041) | 0.0079 vs 0.0019 (0.0079 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.2e-10 vs 5.1e-09 (1.2e-10 vs 5.1e-09) | 1.9e-05 vs 0.00091 (1.9e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 20 | 0.00049 vs 0.0011 (0.00049 vs 0.0011) | 0.00038 vs 0.00062 (0.017 vs 0.018) | 9.1e-06 vs 0.00016 (0.0046 vs 0.0073) | 0.00038 vs 0.0041 (0.00038 vs 0.0041) | 0.0023 vs 0.0019 (0.0023 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.2e-10 vs 5.1e-09 (1.2e-10 vs 5.1e-09) | 2.3e-05 vs 0.00091 (2.3e-05 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 30 | 0.00036 vs 0.0011 (0.00036 vs 0.0011) | 0.00027 vs 0.00062 (0.028 vs 0.018) | 8.8e-06 vs 0.00016 (0.0057 vs 0.0073) | 0.00017 vs 0.0041 (0.00017 vs 0.0041) | 0.0019 vs 0.0019 (0.0019 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.6e-12 vs 5.1e-09 (1.6e-12 vs 5.1e-09) | 6.1e-06 vs 0.00091 (6.1e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.05, cap 40 | 0.00016 vs 0.0011 (0.00016 vs 0.0011) | 0.00015 vs 0.00062 (0.036 vs 0.018) | 7.3e-06 vs 0.00016 (0.0065 vs 0.0073) | 0.00011 vs 0.0041 (0.00011 vs 0.0041) | 0.00072 vs 0.0019 (0.00072 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.5e-12 vs 5.1e-09 (1.5e-12 vs 5.1e-09) | 3e-06 vs 0.00091 (3e-06 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 10 | 0.00016 vs 0.0011 (0.00016 vs 0.0011) | 9.8e-05 vs 0.00062 (0.004 vs 0.018) | 6.8e-06 vs 0.00016 (0.0011 vs 0.0073) | 2.5e-05 vs 0.0041 (2.5e-05 vs 0.0041) | 0.00065 vs 0.0019 (0.00065 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | 1.2e-12 vs 5.1e-09 (1.2e-12 vs 5.1e-09) | 6.5e-07 vs 0.00091 (6.5e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 20 | 0.00015 vs 0.0011 (0.00015 vs 0.0011) | 8.4e-05 vs 0.00062 (0.0096 vs 0.018) | 1.9e-06 vs 0.00016 (0.0025 vs 0.0073) | 2.8e-05 vs 0.0041 (2.8e-05 vs 0.0041) | 0.00058 vs 0.0019 (0.00058 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 6.8e-07 vs 0.00091 (6.8e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 30 | 2.2e-05 vs 0.0011 (2.2e-05 vs 0.0011) | 4.3e-05 vs 0.00062 (0.016 vs 0.018) | 1.6e-06 vs 0.00016 (0.0035 vs 0.0073) | 3e-05 vs 0.0041 (3e-05 vs 0.0041) | 0.00019 vs 0.0019 (0.00019 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 7e-07 vs 0.00091 (7e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.02, cap 40 | 2.1e-05 vs 0.0011 (2.1e-05 vs 0.0011) | 3.6e-05 vs 0.00062 (0.022 vs 0.018) | 3.6e-07 vs 0.00016 (0.0045 vs 0.0073) | 2.3e-05 vs 0.0041 (2.3e-05 vs 0.0041) | 0.00017 vs 0.0019 (0.00017 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 5.8e-07 vs 0.00091 (5.8e-07 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 10 | 0.00014 vs 0.0011 (0.00014 vs 0.0011) | 6.1e-05 vs 0.00062 (0.0012 vs 0.018) | 1.5e-06 vs 0.00016 (0.00072 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.00053 vs 0.0019 (0.00053 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | <1e-12 vs 0.00091 (<1e-12 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 20 | 1.4e-05 vs 0.0011 (1.4e-05 vs 0.0011) | 2.4e-05 vs 0.00062 (0.0053 vs 0.018) | 3.6e-07 vs 0.00016 (0.0019 vs 0.0073) | 5.6e-06 vs 0.0041 (5.6e-06 vs 0.0041) | 0.00014 vs 0.0019 (0.00014 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 7.4e-08 vs 0.00091 (7.4e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 30 | 6.4e-06 vs 0.0011 (6.4e-06 vs 0.0011) | 1.2e-05 vs 0.00062 (0.011 vs 0.018) | 2.8e-07 vs 0.00016 (0.0026 vs 0.0073) | 3.9e-06 vs 0.0041 (3.9e-06 vs 0.0041) | 5.1e-05 vs 0.0019 (5.1e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 3.4e-08 vs 0.00091 (3.4e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.01, cap 40 | 5.9e-06 vs 0.0011 (5.9e-06 vs 0.0011) | 9e-06 vs 0.00062 (0.016 vs 0.018) | 7.7e-08 vs 0.00016 (0.0033 vs 0.0073) | 2.6e-06 vs 0.0041 (2.6e-06 vs 0.0041) | 4.2e-05 vs 0.0019 (4.2e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 2.2e-08 vs 0.00091 (2.2e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 10 | 1.3e-05 vs 0.0011 (1.3e-05 vs 0.0011) | 1.7e-05 vs 0.00062 (0.00077 vs 0.018) | 2.6e-07 vs 0.00016 (0.00043 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 0.00012 vs 0.0019 (0.00012 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | <1e-12 vs 0.00091 (<1e-12 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 20 | 5.9e-06 vs 0.0011 (5.9e-06 vs 0.0011) | 8.2e-06 vs 0.00062 (0.0034 vs 0.018) | 7.6e-08 vs 0.00016 (0.001 vs 0.0073) | 1.5e-06 vs 0.0041 (1.5e-06 vs 0.0041) | 4.2e-05 vs 0.0019 (4.2e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.6e-08 vs 0.00091 (1.6e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 30 | 9.3e-07 vs 0.0011 (9.3e-07 vs 0.0011) | 3.8e-06 vs 0.00062 (0.0071 vs 0.018) | 6.2e-08 vs 0.00016 (0.0017 vs 0.0073) | 1.5e-06 vs 0.0041 (1.5e-06 vs 0.0041) | 1.3e-05 vs 0.0019 (1.3e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 1.6e-08 vs 0.00091 (1.6e-08 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.005, cap 40 | 5.7e-07 vs 0.0011 (5.7e-07 vs 0.0011) | 2.6e-06 vs 0.00062 (0.011 vs 0.018) | 1.1e-08 vs 0.00016 (0.0026 vs 0.0073) | 5e-07 vs 0.0041 (5e-07 vs 0.0041) | 1e-05 vs 0.0019 (1e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 2.4e-09 vs 0.00091 (2.4e-09 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 10 | 5.5e-06 vs 0.0011 (5.5e-06 vs 0.0011) | 5.8e-06 vs 0.00062 (0.00045 vs 0.018) | 2.6e-07 vs 0.00016 (0.00043 vs 0.0073) | <1e-12 vs 0.0041 (<1e-12 vs 0.0041) | 3.7e-05 vs 0.0019 (3.7e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | <1e-12 vs 0.00091 (<1e-12 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 20 | 5.7e-07 vs 0.0011 (5.7e-07 vs 0.0011) | 2.5e-06 vs 0.00062 (0.0028 vs 0.018) | 1.1e-08 vs 0.00016 (0.00067 vs 0.0073) | 4.2e-07 vs 0.0041 (4.2e-07 vs 0.0041) | 1e-05 vs 0.0019 (1e-05 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 2.3e-09 vs 0.00091 (2.3e-09 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 30 | 2.6e-07 vs 0.0011 (2.6e-07 vs 0.0011) | 1.2e-06 vs 0.00062 (0.0051 vs 0.018) | 1.1e-08 vs 0.00016 (0.0014 vs 0.0073) | 2e-07 vs 0.0041 (2e-07 vs 0.0041) | 3.9e-06 vs 0.0019 (3.9e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 7.2e-10 vs 0.00091 (7.2e-10 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.003, cap 40 | 2.3e-07 vs 0.0011 (2.3e-07 vs 0.0011) | 9.3e-07 vs 0.00062 (0.0084 vs 0.018) | 1.1e-08 vs 0.00016 (0.0019 vs 0.0073) | 1.8e-07 vs 0.0041 (1.8e-07 vs 0.0041) | 3.1e-06 vs 0.0019 (3.1e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 6.2e-10 vs 0.00091 (6.2e-10 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 20 | 5.4e-07 vs 0.0011 (5.4e-07 vs 0.0011) | 2.1e-06 vs 0.00062 (0.0015 vs 0.018) | 1.1e-08 vs 0.00016 (0.00067 vs 0.0073) | 1.3e-07 vs 0.0041 (1.3e-07 vs 0.0041) | 9.7e-06 vs 0.0019 (9.7e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 5.2e-10 vs 0.00091 (5.2e-10 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 30 | 2.3e-07 vs 0.0011 (2.3e-07 vs 0.0011) | 8.5e-07 vs 0.00062 (0.0046 vs 0.018) | 2.5e-09 vs 0.00016 (0.0011 vs 0.0073) | 1.1e-07 vs 0.0041 (1.1e-07 vs 0.0041) | 3.1e-06 vs 0.0019 (3.1e-06 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 4.4e-10 vs 0.00091 (4.4e-10 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.002, cap 40 | 2.3e-08 vs 0.0011 (2.3e-08 vs 0.0011) | 2.8e-07 vs 0.00062 (0.0066 vs 0.018) | 2.4e-09 vs 0.00016 (0.0017 vs 0.0073) | 4.5e-08 vs 0.0041 (4.5e-08 vs 0.0041) | 7.5e-07 vs 0.0019 (7.5e-07 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 8.6e-11 vs 0.00091 (8.6e-11 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 20 | 2.3e-08 vs 0.0011 (2.3e-08 vs 0.0011) | 2.4e-07 vs 0.00062 (0.00087 vs 0.018) | 2.4e-09 vs 0.00016 (0.00028 vs 0.0073) | 2.6e-08 vs 0.0041 (2.6e-08 vs 0.0041) | 7.3e-07 vs 0.0019 (7.3e-07 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 6.5e-11 vs 0.00091 (6.5e-11 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 30 | 2.3e-08 vs 0.0011 (2.3e-08 vs 0.0011) | 2.5e-07 vs 0.00062 (0.0026 vs 0.018) | 2.3e-09 vs 0.00016 (0.00068 vs 0.0073) | 3.2e-08 vs 0.0041 (3.2e-08 vs 0.0041) | 7.4e-07 vs 0.0019 (7.4e-07 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 7e-11 vs 0.00091 (7e-11 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.001, cap 40 | 2.1e-08 vs 0.0011 (2.1e-08 vs 0.0011) | 2.2e-07 vs 0.00062 (0.0045 vs 0.018) | 4.4e-10 vs 0.00016 (0.0013 vs 0.0073) | 1.4e-08 vs 0.0041 (1.4e-08 vs 0.0041) | 7e-07 vs 0.0019 (7e-07 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | 2e-11 vs 0.00091 (2e-11 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.0001, cap 20 | 7.9e-10 vs 0.0011 (7.9e-10 vs 0.0011) | 1.6e-08 vs 0.00062 (0.00015 vs 0.018) | 1.7e-11 vs 0.00016 (9.4e-05 vs 0.0073) | 2.9e-10 vs 0.0041 (2.9e-10 vs 0.0041) | 4.4e-08 vs 0.0019 (4.4e-08 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | <1e-12 vs 0.00091 (<1e-12 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.0001, cap 30 | 3.3e-10 vs 0.0011 (3.3e-10 vs 0.0011) | 6.2e-09 vs 0.00062 (0.00069 vs 0.018) | 3.8e-12 vs 0.00016 (0.00019 vs 0.0073) | 1.6e-10 vs 0.0041 (1.6e-10 vs 0.0041) | 1.4e-08 vs 0.0019 (1.4e-08 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | <1e-12 vs 0.00091 (<1e-12 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |
| delta 0.05, alpha 0.0001, cap 40 | 3.4e-11 vs 0.0011 (3.4e-11 vs 0.0011) | 2.3e-09 vs 0.00062 (0.0015 vs 0.018) | 3.5e-12 vs 0.00016 (0.00038 vs 0.0073) | 7.4e-11 vs 0.0041 (7.4e-11 vs 0.0041) | 3.7e-09 vs 0.0019 (3.7e-09 vs 0.0019) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) | <1e-12 vs 5.1e-09 (<1e-12 vs 5.1e-09) | <1e-12 vs 0.00091 (<1e-12 vs 0.00091) | <1e-12 vs <1e-12 (<1e-12 vs <1e-12) |

Per group, the current rule against delta 0.02, alpha 0.01, cap 20, delta 0.03, alpha 0.003, cap 20: the false-switch rate at gain 0 (m equal challengers; in brackets, with the group's contest effect added), and the power at 5% and 10%:

| group | current: rate (contest effect) | 5% | 10% | d 0.02 a 0.01 c 20: rate (contest effect) | 5% | 10% | d 0.03 a 0.003 c 20: rate (contest effect) | 5% | 10% |
|---|---|---|---|---|---|---|---|---|---|
| dev2-joint | 0.0011 (0.0011) | 0.112 | 0.735 | 0.00075 (0.00075) | 0.026 | 0.867 | 2.3e-05 (2.3e-05) | 0.002 | 0.704 |
| dev2-gpu-single | 0.00062 (0.018) | 0.029 | 0.210 | 0.00045 (0.018) | 0.034 | 0.183 | 2.5e-05 (0.0066) | 0.011 | 0.096 |
| dev2-gpu-kernels | 0.00016 (0.0073) | 0.041 | 0.598 | 6.7e-06 (0.039) | 0.173 | 0.801 | 6.9e-08 (0.0062) | 0.042 | 0.444 |
| dev3-joint | 0.0041 (0.0041) | 0.075 | 0.339 | 0.00017 (0.00017) | 0.018 | 0.212 | 2e-05 (2e-05) | 0.004 | 0.117 |
| dev3-gpu-single | 0.0019 (0.0019) | 0.089 | 0.658 | 0.0024 (0.0024) | 0.157 | 0.861 | 0.00017 (0.00017) | 0.040 | 0.650 |
| dev3-gpu-kernels | <1e-12 (<1e-12) | 0.083 | 1.000 | <1e-12 (9.6e-12) | 1.000 | 1.000 | <1e-12 (<1e-12) | 0.976 | 1.000 |
| dev4-joint | 5.1e-09 (5.1e-09) | 0.037 | 0.993 | 1.9e-07 (1.9e-07) | 0.268 | 1.000 | <1e-12 (<1e-12) | 0.012 | 0.999 |
| dev4-gpu-single | 0.00091 (0.00091) | 0.081 | 0.340 | 8.8e-05 (8.8e-05) | 0.021 | 0.096 | 7.5e-07 (7.5e-07) | 0.005 | 0.036 |
| dev4-gpu-kernels | <1e-12 (<1e-12) | 0.052 | 1.000 | <1e-12 (<1e-12) | 1.000 | 1.000 | <1e-12 (<1e-12) | 1.000 | 1.000 |

## The null

### dev2-joint: 331 rounds, 32 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.2613 | 0.0934 | -0.0400 | -1.410 | -0.775 | -0.419 | +0.353 | +0.682 | +1.114 | 0.332 (110) [0.282, 0.386] | 0.580 |

- Load (1-min) 1.4-3.1, median 1.5; the preference's time per round 7.7e-04-0.00451 s, median 0.00112.
- Order: mean x -0.0427 with the A/A arm after the preference (167 rounds), -0.0373 before it (164).
- Successive rounds: lag-1 correlation -0.024; contest means vary 0.45x what independent rounds give (32 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.3108 (32), n=4096 0.2909 (32).
- Distinct challengers per round (most common): 1.

### dev2-gpu-single: 312 rounds, 32 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.3068 | 0.1379 | +0.0057 | -1.557 | -0.990 | -0.557 | +0.431 | +0.814 | +0.935 | 0.279 (87) [0.23, 0.332] | 0.462 |

- Load (1-min) 1.4-3.1, median 1.5; the preference's time per round 4.4e-04-0.0113 s, median 0.00247.
- Order: mean x +0.0046 with the A/A arm after the preference (170 rounds), +0.0070 before it (142).
- Successive rounds: lag-1 correlation 0.065; contest means vary 1.11x what independent rounds give (32 contests): a contest effect of sd 0.0485.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.2802 (32), single=cpu 0.2626 (32).
- Distinct challengers per round (most common): 1.

### dev2-gpu-kernels: 277 rounds, 8 contests (gravity-dev2)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.1228 | 0.0527 | +0.0102 | -0.345 | -0.302 | -0.126 | +0.195 | +0.301 | +1.058 | 0.202 (56) [0.156, 0.254] | 0.484 |

- Load (1-min) 1.4-2.1, median 1.6; the preference's time per round 0.00804-0.0125 s, median 0.00891.
- Order: mean x -0.0052 with the A/A arm after the preference (140 rounds), +0.0260 before it (137).
- Successive rounds: lag-1 correlation -0.011; contest means vary 1.68x what independent rounds give (8 contests): a contest effect of sd 0.0246.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.1006 (8), kern:coarse:256=tierb_256_c16p8t2w@64 0.0642 (4), kern:coarse:256=tierb_256_c16p8t4w@64 0.1985 (3), kern:gateway:512=elect 0.0815 (3), kern:sparse:hier=compact 0.0920 (2).
- Distinct challengers per round (most common): 3.

### dev3-joint: 309 rounds, 32 contests (gravity-dev3)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.1873 | 0.2033 | -0.0161 | -0.435 | -0.370 | -0.282 | +0.318 | +0.391 | +0.426 | 0.453 (140) [0.397, 0.51] | 0.566 |

- Load (1-min) 0.4-2.9, median 1.1; the preference's time per round 0.00559-0.013 s, median 0.00902.
- Order: mean x -0.1508 with the A/A arm after the preference (162 rounds), +0.1324 before it (147).
- Successive rounds: lag-1 correlation -0.609; contest means vary 0.08x what independent rounds give (32 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.2687 (32), n=4096 0.1333 (32).
- Distinct challengers per round (most common): 1.

### dev3-gpu-single: 387 rounds, 32 contests (gravity-dev3)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.1424 | 0.0843 | -0.0296 | -0.640 | -0.577 | -0.332 | +0.141 | +0.261 | +0.419 | 0.32 (124) [0.274, 0.369] | 0.540 |

- Load (1-min) 0.4-3.2, median 1.1; the preference's time per round 0.00133-0.028 s, median 0.00779.
- Order: mean x -0.0545 with the A/A arm after the preference (200 rounds), -0.0031 before it (187).
- Successive rounds: lag-1 correlation -0.037; contest means vary 0.58x what independent rounds give (32 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.2089 (32), single=cpu 0.3348 (32).
- Distinct challengers per round (most common): 1.

### dev3-gpu-kernels: 320 rounds, 11 contests (gravity-dev3)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0153 | 0.0100 | -0.0006 | -0.099 | -0.041 | -0.020 | +0.019 | +0.027 | +0.094 | 0.00625 (2) [7.6e-04, 0.0224] | 0.544 |

- Load (1-min) 0.8-3.2, median 1.2; the preference's time per round 0.0711-0.097 s, median 0.082.
- Order: mean x +0.0005 with the A/A arm after the preference (164 rounds), -0.0017 before it (156).
- Successive rounds: lag-1 correlation -0.200; contest means vary 1.15x what independent rounds give (11 contests): a contest effect of sd 0.0019.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0135 (11), kern:coarse:256=tierb_256_c16p4t8w 0.1014 (10), kern:coarse:256=tierb_256_c16p4t8w,kern:gateway:512=elect 0.0438 (1), kern:coarse:256=tierb_256_c16p4t8w,kern:sparse:hier=compact 0.0631 (1), kern:gateway:512=elect 0.0146 (1).
- Distinct challengers per round (most common): 3.

### dev4-joint: 288 rounds, 32 contests (gravity-dev4)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0421 | 0.0408 | -0.0045 | -0.132 | -0.097 | -0.061 | +0.054 | +0.084 | +0.251 | 0.0972 (28) [0.0656, 0.137] | 0.562 |

- Load (1-min) 0.4-0.9, median 0.6; the preference's time per round 0.00728-0.0132 s, median 0.0108.
- Order: mean x -0.0255 with the A/A arm after the preference (160 rounds), +0.0216 before it (128).
- Successive rounds: lag-1 correlation -0.454; contest means vary 0.83x what independent rounds give (32 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0287 (32), n=4096 0.0365 (32).
- Distinct challengers per round (most common): 1.

### dev4-gpu-single: 476 rounds, 32 contests (gravity-dev4)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.2198 | 0.2332 | -0.0320 | -0.584 | -0.484 | -0.405 | +0.299 | +0.549 | +0.672 | 0.437 (208) [0.392, 0.483] | 0.567 |

- Load (1-min) 0.4-0.9, median 0.6; the preference's time per round 0.00136-0.0182 s, median 0.00624.
- Order: mean x -0.1996 with the A/A arm after the preference (239 rounds), +0.1371 before it (237).
- Successive rounds: lag-1 correlation -0.506; contest means vary 0.25x what independent rounds give (32 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.2219 (32), single=cpu 0.3872 (32).
- Distinct challengers per round (most common): 1.

### dev4-gpu-kernels: 216 rounds, 8 contests (gravity-dev4)

| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0048 | 0.0046 | +0.0003 | -0.012 | -0.011 | -0.007 | +0.009 | +0.012 | +0.013 | 0 (0) [0, 0.0169] | 0.486 |

- Load (1-min) 0.3-0.9, median 0.5; the preference's time per round 0.105-0.127 s, median 0.113.
- Order: mean x +0.0008 with the A/A arm after the preference (112 rounds), -0.0003 before it (104).
- Successive rounds: lag-1 correlation -0.063; contest means vary 0.25x what independent rounds give (8 contests): a contest effect of sd 0.0000.
- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): A/A 0.0056 (8), kern:coarse:256=tierb_256_c16p4@16 0.0062 (8), kern:gateway:512=elect 0.0045 (8), kern:sparse:hier=compact 0.0074 (8).
- Distinct challengers per round (most common): 3.

## Dependence on load, work and place in the contest

### dev2-joint

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 1.36-1.51 | 54 | 0.2704 | 0.1185 | 0.296 |
| load (1-min) | 1.51-1.53 | 65 | 0.2793 | 0.0745 | 0.2 |
| load (1-min) | 1.53-1.55 | 54 | 0.1709 | 0.0831 | 0.333 |
| load (1-min) | 1.55-1.88 | 90 | 0.2767 | 0.1070 | 0.389 |
| load (1-min) | 1.88-3.14 | 68 | 0.2579 | 0.1358 | 0.412 |
| preference's time (s) | 7.7e-04-9.8e-04 | 66 | 0.1227 | 0.0546 | 0.167 |
| preference's time (s) | 9.8e-04-0.0011 | 66 | 0.2104 | 0.0695 | 0.273 |
| preference's time (s) | 0.0011-0.00113 | 66 | 0.1756 | 0.0289 | 0.182 |
| preference's time (s) | 0.00113-0.00122 | 66 | 0.1563 | 0.0916 | 0.182 |
| preference's time (s) | 0.00122-0.00451 | 67 | 0.3210 | 0.1025 | 0.851 |
| timed runs in the round | 2.5-3.5 | 331 | 0.2613 | 0.0934 | 0.332 |
| round of the contest | 1-2 | 32 | 0.0403 | 0.0259 | 0.188 |
| round of the contest | 2-4 | 64 | 0.3158 | 0.1391 | 0.75 |
| round of the contest | 4-6 | 37 | 0.2586 | 0.0507 | 0.135 |
| round of the contest | 6-11 | 20 | 0.1082 | 0.1212 | 0.45 |
| round of the contest | 11-21 | 40 | 0.1620 | 0.0477 | 0.075 |
| round of the contest | 21-1e+03 | 138 | 0.2655 | 0.0801 | 0.283 |

### dev2-gpu-single

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 1.36-1.51 | 60 | 0.2691 | 0.1101 | 0.333 |
| load (1-min) | 1.51-1.53 | 64 | 0.3006 | 0.0754 | 0.156 |
| load (1-min) | 1.53-1.55 | 58 | 0.3832 | 0.2208 | 0.414 |
| load (1-min) | 1.55-1.81 | 62 | 0.2624 | 0.1629 | 0.274 |
| load (1-min) | 1.81-3.14 | 68 | 0.3089 | 0.1874 | 0.235 |
| preference's time (s) | 4.4e-04-8.7e-04 | 63 | 0.1749 | 0.1117 | 0.143 |
| preference's time (s) | 8.7e-04-0.00205 | 62 | 0.3071 | 0.0552 | 0.113 |
| preference's time (s) | 0.00205-0.00309 | 62 | 0.2917 | 0.2244 | 0.226 |
| preference's time (s) | 0.00309-0.0042 | 62 | 0.3220 | 0.1166 | 0.306 |
| preference's time (s) | 0.0042-0.0113 | 63 | 0.3120 | 0.2230 | 0.603 |
| timed runs in the round | 2.5-3.5 | 312 | 0.3068 | 0.1379 | 0.279 |
| round of the contest | 1-2 | 32 | 0.1162 | 0.1667 | 0.156 |
| round of the contest | 2-4 | 64 | 0.3878 | 0.1902 | 0.234 |
| round of the contest | 4-6 | 10 | 0.2888 | 0.2597 | 0.5 |
| round of the contest | 6-11 | 20 | 0.1743 | 0.0802 | 0.3 |
| round of the contest | 11-21 | 40 | 0.3815 | 0.0951 | 0.35 |
| round of the contest | 21-1e+03 | 146 | 0.2794 | 0.1303 | 0.288 |

### dev2-gpu-kernels

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 1.36-1.5 | 49 | 0.0872 | 0.0681 | 0.245 |
| load (1-min) | 1.5-1.54 | 52 | 0.2020 | 0.0537 | 0.154 |
| load (1-min) | 1.54-1.57 | 61 | 0.1093 | 0.0948 | 0.344 |
| load (1-min) | 1.57-1.6 | 56 | 0.0969 | 0.0513 | 0.125 |
| load (1-min) | 1.6-2.08 | 59 | 0.0758 | 0.0279 | 0.136 |
| preference's time (s) | 0.00804-0.00856 | 56 | 0.0732 | 0.0278 | 0.0179 |
| preference's time (s) | 0.00856-0.00878 | 55 | 0.0817 | 0.0351 | 0 |
| preference's time (s) | 0.00878-0.00904 | 55 | 0.0603 | 0.0269 | 0.0364 |
| preference's time (s) | 0.00904-0.00954 | 55 | 0.0817 | 0.0534 | 0.309 |
| preference's time (s) | 0.00954-0.0125 | 56 | 0.2169 | 0.0918 | 0.643 |
| timed runs in the round | 2.5-3.5 | 20 | 0.1106 | 0.0443 | 0.2 |
| timed runs in the round | 3.5-4.5 | 6 | 0.1134 | 0.0335 | 0 |
| timed runs in the round | 4.5-99 | 251 | 0.1242 | 0.0530 | 0.207 |
| round of the contest | 1-2 | 8 | 0.0380 | 0.0192 | 0.125 |
| round of the contest | 2-4 | 16 | 0.3461 | 0.0699 | 0.312 |
| round of the contest | 4-6 | 11 | 0.0579 | 0.0719 | 0.455 |
| round of the contest | 6-11 | 20 | 0.0995 | 0.0499 | 0.2 |
| round of the contest | 11-21 | 40 | 0.1082 | 0.0504 | 0.225 |
| round of the contest | 21-1e+03 | 182 | 0.0927 | 0.0496 | 0.176 |

### dev3-joint

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.437-0.837 | 62 | 0.1602 | 0.1401 | 0.435 |
| load (1-min) | 0.837-1.04 | 51 | 0.2028 | 0.1923 | 0.451 |
| load (1-min) | 1.04-1.27 | 70 | 0.2245 | 0.2586 | 0.5 |
| load (1-min) | 1.27-2.1 | 61 | 0.1980 | 0.2237 | 0.557 |
| load (1-min) | 2.1-2.88 | 65 | 0.1423 | 0.1566 | 0.323 |
| preference's time (s) | 0.00559-0.00775 | 62 | 0.1301 | 0.1198 | 0.21 |
| preference's time (s) | 0.00775-0.00862 | 62 | 0.1780 | 0.2390 | 0.242 |
| preference's time (s) | 0.00862-0.00953 | 61 | 0.1498 | 0.1719 | 0.262 |
| preference's time (s) | 0.00953-0.0107 | 62 | 0.1577 | 0.1677 | 0.581 |
| preference's time (s) | 0.0107-0.013 | 62 | 0.0934 | 0.0844 | 0.968 |
| timed runs in the round | 2.5-3.5 | 309 | 0.1873 | 0.2033 | 0.453 |
| round of the contest | 1-2 | 32 | 0.0617 | 0.0540 | 0.969 |
| round of the contest | 2-4 | 64 | 0.2897 | 0.4170 | 0.5 |
| round of the contest | 4-6 | 21 | 0.1151 | 0.0726 | 0.333 |
| round of the contest | 6-11 | 20 | 0.1828 | 0.1358 | 0.3 |
| round of the contest | 11-21 | 40 | 0.1736 | 0.2043 | 0.375 |
| round of the contest | 21-1e+03 | 132 | 0.1371 | 0.1407 | 0.371 |

### dev3-gpu-single

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.437-0.857 | 77 | 0.1297 | 0.0818 | 0.351 |
| load (1-min) | 0.857-1.04 | 69 | 0.1499 | 0.0732 | 0.217 |
| load (1-min) | 1.04-1.56 | 85 | 0.1700 | 0.1012 | 0.388 |
| load (1-min) | 1.56-2.1 | 66 | 0.1642 | 0.0929 | 0.318 |
| load (1-min) | 2.1-3.25 | 90 | 0.0929 | 0.0881 | 0.311 |
| preference's time (s) | 0.00133-0.00389 | 78 | 0.2563 | 0.2128 | 0.513 |
| preference's time (s) | 0.00389-0.00649 | 77 | 0.1040 | 0.0963 | 0.351 |
| preference's time (s) | 0.00649-0.00919 | 77 | 0.0719 | 0.0740 | 0.273 |
| preference's time (s) | 0.00919-0.0111 | 77 | 0.0558 | 0.0591 | 0.13 |
| preference's time (s) | 0.0111-0.028 | 78 | 0.0872 | 0.0676 | 0.333 |
| timed runs in the round | 2.5-3.5 | 387 | 0.1424 | 0.0843 | 0.32 |
| round of the contest | 1-2 | 32 | 0.1864 | 0.1783 | 0.5 |
| round of the contest | 2-4 | 64 | 0.2459 | 0.1813 | 0.484 |
| round of the contest | 4-6 | 33 | 0.0666 | 0.0522 | 0.152 |
| round of the contest | 6-11 | 20 | 0.0970 | 0.0885 | 0.3 |
| round of the contest | 11-21 | 40 | 0.1235 | 0.0723 | 0.4 |
| round of the contest | 21-1e+03 | 198 | 0.0862 | 0.0732 | 0.253 |

### dev3-gpu-kernels

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.812-1.02 | 58 | 0.0125 | 0.0091 | 0.0172 |
| load (1-min) | 1.02-1.13 | 70 | 0.0112 | 0.0111 | 0 |
| load (1-min) | 1.13-1.27 | 60 | 0.0136 | 0.0133 | 0 |
| load (1-min) | 1.27-2.25 | 64 | 0.0186 | 0.0097 | 0 |
| load (1-min) | 2.25-3.25 | 68 | 0.0187 | 0.0099 | 0.0147 |
| preference's time (s) | 0.0711-0.0771 | 64 | 0.0123 | 0.0142 | 0 |
| preference's time (s) | 0.0771-0.0811 | 64 | 0.0139 | 0.0087 | 0.0156 |
| preference's time (s) | 0.0811-0.083 | 64 | 0.0124 | 0.0084 | 0 |
| preference's time (s) | 0.083-0.0851 | 64 | 0.0106 | 0.0093 | 0 |
| preference's time (s) | 0.0851-0.097 | 64 | 0.0236 | 0.0132 | 0.0156 |
| timed runs in the round | 2.5-3.5 | 100 | 0.0125 | 0.0115 | 0.01 |
| timed runs in the round | 4.5-99 | 216 | 0.0165 | 0.0095 | 0.00463 |
| round of the contest | 1-2 | 11 | 0.0106 | 0.0078 | 0 |
| round of the contest | 2-4 | 22 | 0.0141 | 0.0176 | 0 |
| round of the contest | 4-6 | 15 | 0.0071 | 0.0025 | 0 |
| round of the contest | 6-11 | 20 | 0.0392 | 0.0109 | 0.05 |
| round of the contest | 11-21 | 40 | 0.0109 | 0.0077 | 0 |
| round of the contest | 21-1e+03 | 212 | 0.0128 | 0.0104 | 0.00472 |

### dev4-joint

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.427-0.574 | 54 | 0.0278 | 0.0282 | 0.0556 |
| load (1-min) | 0.574-0.618 | 49 | 0.0272 | 0.0245 | 0.0408 |
| load (1-min) | 0.618-0.668 | 68 | 0.0571 | 0.0526 | 0.103 |
| load (1-min) | 0.668-0.751 | 58 | 0.0421 | 0.0463 | 0.103 |
| load (1-min) | 0.751-0.87 | 59 | 0.0427 | 0.0451 | 0.169 |
| preference's time (s) | 0.00728-0.00909 | 58 | 0.0567 | 0.0486 | 0.0517 |
| preference's time (s) | 0.00909-0.0105 | 57 | 0.0442 | 0.0517 | 0.123 |
| preference's time (s) | 0.0105-0.0111 | 58 | 0.0312 | 0.0324 | 0.121 |
| preference's time (s) | 0.0111-0.0114 | 57 | 0.0222 | 0.0178 | 0.0351 |
| preference's time (s) | 0.0114-0.0132 | 58 | 0.0413 | 0.0440 | 0.155 |
| timed runs in the round | 2.5-3.5 | 288 | 0.0421 | 0.0408 | 0.0972 |
| round of the contest | 1-2 | 32 | 0.0097 | 0.0070 | 0 |
| round of the contest | 2-4 | 64 | 0.0240 | 0.0172 | 0.109 |
| round of the contest | 4-6 | 8 | 0.0257 | 0.0280 | 0 |
| round of the contest | 6-11 | 20 | 0.0461 | 0.0489 | 0.1 |
| round of the contest | 11-21 | 40 | 0.0464 | 0.0575 | 0.2 |
| round of the contest | 21-1e+03 | 124 | 0.0499 | 0.0496 | 0.0887 |

### dev4-gpu-single

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.377-0.489 | 95 | 0.2362 | 0.3125 | 0.463 |
| load (1-min) | 0.489-0.586 | 95 | 0.2073 | 0.2383 | 0.516 |
| load (1-min) | 0.586-0.639 | 90 | 0.2086 | 0.2146 | 0.411 |
| load (1-min) | 0.639-0.696 | 96 | 0.2169 | 0.2011 | 0.427 |
| load (1-min) | 0.696-0.899 | 100 | 0.2209 | 0.2012 | 0.37 |
| preference's time (s) | 0.00136-0.00363 | 95 | 0.3363 | 0.2026 | 0.737 |
| preference's time (s) | 0.00363-0.00539 | 95 | 0.1491 | 0.1604 | 0.147 |
| preference's time (s) | 0.00539-0.00678 | 95 | 0.1870 | 0.2398 | 0.389 |
| preference's time (s) | 0.00678-0.00863 | 95 | 0.1654 | 0.1903 | 0.474 |
| preference's time (s) | 0.00863-0.0182 | 96 | 0.1139 | 0.0661 | 0.438 |
| timed runs in the round | 2.5-3.5 | 476 | 0.2198 | 0.2332 | 0.437 |
| round of the contest | 1-2 | 32 | 0.0543 | 0.0479 | 1 |
| round of the contest | 2-4 | 64 | 0.2453 | 0.3660 | 0.5 |
| round of the contest | 4-6 | 36 | 0.0480 | 0.0284 | 0.139 |
| round of the contest | 6-11 | 20 | 0.0774 | 0.0644 | 0.35 |
| round of the contest | 11-21 | 40 | 0.2240 | 0.1767 | 0.425 |
| round of the contest | 21-1e+03 | 284 | 0.2204 | 0.2528 | 0.405 |

### dev4-gpu-kernels

| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |
|---|---|---|---|---|---|
| load (1-min) | 0.32-0.426 | 42 | 0.0052 | 0.0042 | 0 |
| load (1-min) | 0.426-0.488 | 43 | 0.0044 | 0.0039 | 0 |
| load (1-min) | 0.488-0.592 | 42 | 0.0048 | 0.0050 | 0 |
| load (1-min) | 0.592-0.667 | 42 | 0.0047 | 0.0055 | 0 |
| load (1-min) | 0.667-0.899 | 47 | 0.0048 | 0.0040 | 0 |
| preference's time (s) | 0.105-0.107 | 43 | 0.0058 | 0.0045 | 0 |
| preference's time (s) | 0.107-0.113 | 43 | 0.0044 | 0.0040 | 0 |
| preference's time (s) | 0.113-0.114 | 43 | 0.0043 | 0.0047 | 0 |
| preference's time (s) | 0.114-0.115 | 43 | 0.0034 | 0.0036 | 0 |
| preference's time (s) | 0.115-0.127 | 44 | 0.0057 | 0.0067 | 0 |
| timed runs in the round | 4.5-99 | 216 | 0.0048 | 0.0046 | 0 |
| round of the contest | 1-2 | 8 | 0.0042 | 0.0050 | 0 |
| round of the contest | 2-4 | 16 | 0.0038 | 0.0055 | 0 |
| round of the contest | 4-6 | 8 | 0.0048 | 0.0043 | 0 |
| round of the contest | 6-11 | 20 | 0.0054 | 0.0039 | 0 |
| round of the contest | 11-21 | 40 | 0.0038 | 0.0034 | 0 |
| round of the contest | 21-1e+03 | 124 | 0.0049 | 0.0043 | 0 |

## The current rule's false-switch rate (TIE 5%, 75% share, minimum 5, cap 10)

The first contest draws rounds 1-3 from their own samples and later rounds by parity; the confirmation, a contest that starts later, draws every round from the later rounds (contest rounds after the third, and confirmation rounds), by parity. The last but one column draws the confirmation from the logged confirmation rounds alone (pooled; with the range its 95% interval gives), where at least 20 were logged.

| group | P(round win) [95% CI] | rounds 1 / 2 / 3, later odd / even | contest, m=1 | confirmed, m=1 | confirmed, m | m | confirmed, m, every sample at its 95% CI's upper end | with the contest effect (tau) | confirmed, m, from the logged confirmations [95% CI] (rounds) | rounds (equal arms) |
|---|---|---|---|---|---|---|---|---|---|---|
| dev2-joint | 0.332 [0.282, 0.386] | 0.188 / 1.000 / 0.500 / 0.427 / 0.091 | 0.065 | 0.0011 | 0.0011 | 1 | 0.011 | 0.0011 (0.000) | - | 4.95 |
| dev2-gpu-single | 0.279 [0.23, 0.332] | 0.156 / 0.344 / 0.125 / 0.349 / 0.273 | 0.015 | 0.00062 | 0.00062 | 1 | 0.01 | 0.018 (0.048) | - | 3.85 |
| dev2-gpu-kernels | 0.202 [0.156, 0.254] | 0.218 / 0.178 / 0.218 / 0.218 / 0.178 | 0.0073 | 5.3e-05 | 0.00016 | 3 | 0.0021 | 0.0073 (0.025) | - | 3.74 |
| dev3-joint | 0.453 [0.397, 0.51] | 0.969 / 0.000 / 1.000 / 0.673 / 0.096 | 0.066 | 0.0041 | 0.0041 | 1 | 0.033 | 0.0041 (0.000) | - | 5.69 |
| dev3-gpu-single | 0.32 [0.274, 0.369] | 0.500 / 0.344 / 0.625 / 0.301 / 0.232 | 0.08 | 0.0019 | 0.0019 | 1 | 0.014 | 0.0019 (0.000) | - | 4.76 |
| dev3-gpu-kernels | 0.00625 [7.6e-04, 0.0224] | 0.000 / 0.014 / 0.000 / 0.000 / 0.014 | <1e-12 | <1e-12 | <1e-12 | 3 | 9.8e-11 | <1e-12 (0.002) | - | 3.01 |
| dev4-joint | 0.0972 [0.0656, 0.137] | 0.000 / 0.125 / 0.094 / 0.208 / 0.010 | 2.5e-05 | 5.1e-09 | 5.1e-09 | 1 | 1.7e-05 | 5.1e-09 (0.000) | - | 3.22 |
| dev4-gpu-single | 0.437 [0.392, 0.483] | 1.000 / 0.000 / 1.000 / 0.783 / 0.034 | 0.027 | 0.00091 | 0.00091 | 1 | 0.012 | 0.00091 (0.000) | - | 5.81 |
| dev4-gpu-kernels | 0 [0, 0.0169] | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | <1e-12 | <1e-12 | <1e-12 | 3 | 2.9e-10 | <1e-12 (0.000) | - | 3.00 |

On the logged A/A sequences in their order (contests of at least 10 or 20 rounds, cut into windows from round 1, so a contest's first window holds its first rounds), against the switches the model expects at each window's place:

| group | window | rule | windows | switches | expected (model) |
|---|---|---|---|---|---|
| dev2-joint | 10 | current rule, one contest (no confirmation) | 20 | 2 | 0.526 |
| dev2-joint | 10 | sign test, delta 0, alpha 0.01 | 20 | 0 | 0.0544 |
| dev2-joint | 10 | sign test, delta 0, alpha 0.001 | 20 | 0 | 7.9e-04 |
| dev2-joint | 10 | sign test, delta 0.02, alpha 0.01 | 20 | 0 | 0.0253 |
| dev2-joint | 10 | sign test, delta 0.02, alpha 0.001 | 20 | 0 | 2.5e-04 |
| dev2-joint | 20 | current rule, one contest (no confirmation) | 8 | 1 | 0.328 |
| dev2-joint | 20 | sign test, delta 0, alpha 0.01 | 8 | 0 | 0.0101 |
| dev2-joint | 20 | sign test, delta 0, alpha 0.001 | 8 | 0 | 1.7e-04 |
| dev2-joint | 20 | sign test, delta 0.02, alpha 0.01 | 8 | 0 | 0.00346 |
| dev2-joint | 20 | sign test, delta 0.02, alpha 0.001 | 8 | 0 | 3.5e-05 |
| dev2-gpu-single | 10 | current rule, one contest (no confirmation) | 21 | 1 | 0.767 |
| dev2-gpu-single | 10 | sign test, delta 0, alpha 0.01 | 21 | 0 | 0.139 |
| dev2-gpu-single | 10 | sign test, delta 0, alpha 0.001 | 21 | 0 | 0.0188 |
| dev2-gpu-single | 10 | sign test, delta 0.02, alpha 0.01 | 21 | 0 | 0.0352 |
| dev2-gpu-single | 10 | sign test, delta 0.02, alpha 0.001 | 21 | 0 | 0.00228 |
| dev2-gpu-single | 20 | current rule, one contest (no confirmation) | 9 | 1 | 0.27 |
| dev2-gpu-single | 20 | sign test, delta 0, alpha 0.01 | 9 | 0 | 0.0648 |
| dev2-gpu-single | 20 | sign test, delta 0, alpha 0.001 | 9 | 0 | 0.00447 |
| dev2-gpu-single | 20 | sign test, delta 0.02, alpha 0.01 | 9 | 0 | 0.00834 |
| dev2-gpu-single | 20 | sign test, delta 0.02, alpha 0.001 | 9 | 0 | 2.6e-04 |
| dev2-gpu-kernels | 10 | current rule, one contest (no confirmation) | 25 | 0 | 0.181 |
| dev2-gpu-kernels | 10 | sign test, delta 0, alpha 0.01 | 25 | 0 | 0.154 |
| dev2-gpu-kernels | 10 | sign test, delta 0, alpha 0.001 | 25 | 0 | 0.0153 |
| dev2-gpu-kernels | 10 | sign test, delta 0.02, alpha 0.01 | 25 | 0 | 0.00225 |
| dev2-gpu-kernels | 10 | sign test, delta 0.02, alpha 0.001 | 25 | 0 | 3.4e-05 |
| dev2-gpu-kernels | 20 | current rule, one contest (no confirmation) | 12 | 0 | 0.0871 |
| dev2-gpu-kernels | 20 | sign test, delta 0, alpha 0.01 | 12 | 0 | 0.0716 |
| dev2-gpu-kernels | 20 | sign test, delta 0, alpha 0.001 | 12 | 0 | 0.00424 |
| dev2-gpu-kernels | 20 | sign test, delta 0.02, alpha 0.01 | 12 | 0 | 2.8e-04 |
| dev2-gpu-kernels | 20 | sign test, delta 0.02, alpha 0.001 | 12 | 0 | 1.4e-06 |
| dev3-joint | 10 | current rule, one contest (no confirmation) | 20 | 2 | 1.25 |
| dev3-joint | 10 | sign test, delta 0, alpha 0.01 | 20 | 0 | 0.126 |
| dev3-joint | 10 | sign test, delta 0, alpha 0.001 | 20 | 0 | 0.00669 |
| dev3-joint | 10 | sign test, delta 0.02, alpha 0.01 | 20 | 0 | 0.0234 |
| dev3-joint | 10 | sign test, delta 0.02, alpha 0.001 | 20 | 0 | 4.5e-04 |
| dev3-joint | 20 | current rule, one contest (no confirmation) | 8 | 2 | 0.514 |
| dev3-joint | 20 | sign test, delta 0, alpha 0.01 | 8 | 0 | 0.0355 |
| dev3-joint | 20 | sign test, delta 0, alpha 0.001 | 8 | 0 | 0.00184 |
| dev3-joint | 20 | sign test, delta 0.02, alpha 0.01 | 8 | 0 | 0.00267 |
| dev3-joint | 20 | sign test, delta 0.02, alpha 0.001 | 8 | 0 | 4.9e-05 |
| dev3-gpu-single | 10 | current rule, one contest (no confirmation) | 26 | 2 | 0.832 |
| dev3-gpu-single | 10 | sign test, delta 0, alpha 0.01 | 26 | 1 | 0.31 |
| dev3-gpu-single | 10 | sign test, delta 0, alpha 0.001 | 26 | 0 | 0.04 |
| dev3-gpu-single | 10 | sign test, delta 0.02, alpha 0.01 | 26 | 1 | 0.0559 |
| dev3-gpu-single | 10 | sign test, delta 0.02, alpha 0.001 | 26 | 0 | 0.00298 |
| dev3-gpu-single | 20 | current rule, one contest (no confirmation) | 12 | 0 | 0.508 |
| dev3-gpu-single | 20 | sign test, delta 0, alpha 0.01 | 12 | 0 | 0.183 |
| dev3-gpu-single | 20 | sign test, delta 0, alpha 0.001 | 12 | 0 | 0.0153 |
| dev3-gpu-single | 20 | sign test, delta 0.02, alpha 0.01 | 12 | 0 | 0.0174 |
| dev3-gpu-single | 20 | sign test, delta 0.02, alpha 0.001 | 12 | 0 | 4.9e-04 |
| dev3-gpu-kernels | 10 | current rule, one contest (no confirmation) | 28 | 0 | 0 |
| dev3-gpu-kernels | 10 | sign test, delta 0, alpha 0.01 | 28 | 1 | 0.35 |
| dev3-gpu-kernels | 10 | sign test, delta 0, alpha 0.001 | 28 | 1 | 0.06 |
| dev3-gpu-kernels | 10 | sign test, delta 0.02, alpha 0.01 | 28 | 0 | 1.2e-08 |
| dev3-gpu-kernels | 10 | sign test, delta 0.02, alpha 0.001 | 28 | 0 | 1.9e-12 |
| dev3-gpu-kernels | 20 | current rule, one contest (no confirmation) | 12 | 0 | 0 |
| dev3-gpu-kernels | 20 | sign test, delta 0, alpha 0.01 | 12 | 1 | 0.235 |
| dev3-gpu-kernels | 20 | sign test, delta 0, alpha 0.001 | 12 | 0 | 0.0219 |
| dev3-gpu-kernels | 20 | sign test, delta 0.02, alpha 0.01 | 12 | 0 | 3.5e-10 |
| dev3-gpu-kernels | 20 | sign test, delta 0.02, alpha 0.001 | 12 | 0 | 1.9e-15 |
| dev4-joint | 10 | current rule, one contest (no confirmation) | 20 | 0 | 0.00328 |
| dev4-joint | 10 | sign test, delta 0, alpha 0.01 | 20 | 0 | 0.0129 |
| dev4-joint | 10 | sign test, delta 0, alpha 0.001 | 20 | 0 | 8.4e-05 |
| dev4-joint | 10 | sign test, delta 0.02, alpha 0.01 | 20 | 0 | 1.4e-04 |
| dev4-joint | 10 | sign test, delta 0.02, alpha 0.001 | 20 | 0 | 9.3e-08 |
| dev4-joint | 20 | current rule, one contest (no confirmation) | 8 | 0 | 9.0e-04 |
| dev4-joint | 20 | sign test, delta 0, alpha 0.01 | 8 | 0 | 0.00121 |
| dev4-joint | 20 | sign test, delta 0, alpha 0.001 | 8 | 0 | 1.0e-05 |
| dev4-joint | 20 | sign test, delta 0.02, alpha 0.01 | 8 | 0 | 1.8e-06 |
| dev4-joint | 20 | sign test, delta 0.02, alpha 0.001 | 8 | 0 | 9.4e-10 |
| dev4-gpu-single | 10 | current rule, one contest (no confirmation) | 34 | 0 | 1.1 |
| dev4-gpu-single | 10 | sign test, delta 0, alpha 0.01 | 34 | 0 | 0.154 |
| dev4-gpu-single | 10 | sign test, delta 0, alpha 0.001 | 34 | 0 | 0.00475 |
| dev4-gpu-single | 10 | sign test, delta 0.02, alpha 0.01 | 34 | 0 | 0.0219 |
| dev4-gpu-single | 10 | sign test, delta 0.02, alpha 0.001 | 34 | 0 | 2.1e-04 |
| dev4-gpu-single | 20 | current rule, one contest (no confirmation) | 16 | 0 | 0.507 |
| dev4-gpu-single | 20 | sign test, delta 0, alpha 0.01 | 16 | 0 | 0.0442 |
| dev4-gpu-single | 20 | sign test, delta 0, alpha 0.001 | 16 | 0 | 0.00168 |
| dev4-gpu-single | 20 | sign test, delta 0.02, alpha 0.01 | 16 | 0 | 0.00226 |
| dev4-gpu-single | 20 | sign test, delta 0.02, alpha 0.001 | 16 | 0 | 2.5e-05 |
| dev4-gpu-kernels | 10 | current rule, one contest (no confirmation) | 20 | 0 | 0 |
| dev4-gpu-kernels | 10 | sign test, delta 0, alpha 0.01 | 20 | 0 | 0.153 |
| dev4-gpu-kernels | 10 | sign test, delta 0, alpha 0.001 | 20 | 0 | 0.0211 |
| dev4-gpu-kernels | 10 | sign test, delta 0.02, alpha 0.01 | 20 | 0 | 0 |
| dev4-gpu-kernels | 10 | sign test, delta 0.02, alpha 0.001 | 20 | 0 | 0 |
| dev4-gpu-kernels | 20 | current rule, one contest (no confirmation) | 8 | 0 | 0 |
| dev4-gpu-kernels | 20 | sign test, delta 0, alpha 0.01 | 8 | 0 | 0.0789 |
| dev4-gpu-kernels | 20 | sign test, delta 0, alpha 0.001 | 8 | 0 | 0.00562 |
| dev4-gpu-kernels | 20 | sign test, delta 0.02, alpha 0.01 | 8 | 0 | 0 |
| dev4-gpu-kernels | 20 | sign test, delta 0.02, alpha 0.001 | 8 | 0 | 0 |

## Rules under the dev2-joint null (331 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.0011 | 0.0011 | 0.020 | 0.112 | 0.735 | 5.0 | 5.2 |
| 20 | 0.0011 | 0.0011 | 0.020 | 0.113 | 0.828 | 8.2 | 5.8 |
| 30 | 0.0011 | 0.0011 | 0.020 | 0.113 | 0.854 | 9.6 | 6.1 |
| 40 | 0.0011 | 0.0011 | 0.020 | 0.113 | 0.877 | 11.4 | 6.5 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0086 | 0.0086 | 0.016 | 0.221 | 0.545 | 3.7 | 4.9 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0021 | 0.0021 | 0.006 | 0.396 | 0.920 | 9.7 | 13.1 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.002 | 0.002 | 0.006 | 0.622 | 0.994 | 17.7 | 20.6 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0019 | 0.0019 | 0.007 | 0.745 | 0.999 | 23.7 | 24.5 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.00012 | 0.00012 | 0.000 | 0.062 | 0.369 | 3.7 | 5.4 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 3.7e-05 | 3.7e-05 | 0.000 | 0.135 | 0.722 | 7.7 | 12.4 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 4.6e-05 | 4.6e-05 | 0.000 | 0.281 | 0.940 | 13.7 | 21.3 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 3.4e-05 | 3.4e-05 | 0.000 | 0.405 | 0.988 | 19.7 | 29.1 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 2.3e-06 | 2.3e-06 | 0.000 | 0.037 | 0.438 | 5.7 | 9.2 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 2e-06 | 2e-06 | 0.000 | 0.104 | 0.820 | 11.7 | 19.8 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 5.9e-07 | 5.9e-07 | 0.000 | 0.187 | 0.953 | 17.7 | 29.7 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0042 | 0.0042 | 0.009 | 0.039 | 0.489 | 3.2 | 4.1 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00075 | 0.00075 | 0.002 | 0.026 | 0.867 | 8.8 | 11.1 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.00059 | 0.00059 | 0.002 | 0.036 | 0.982 | 16.0 | 20.3 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.00054 | 0.00054 | 0.002 | 0.042 | 0.996 | 21.4 | 27.2 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 4.2e-05 | 4.2e-05 | 0.000 | 0.002 | 0.296 | 3.2 | 4.2 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 7.6e-06 | 7.6e-06 | 0.000 | 0.002 | 0.617 | 7.0 | 8.9 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 8.4e-06 | 8.4e-06 | 0.000 | 0.003 | 0.881 | 12.4 | 15.9 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 6.2e-06 | 6.2e-06 | 0.000 | 0.003 | 0.966 | 17.8 | 23.0 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 4.3e-07 | 4.3e-07 | 0.000 | 0.000 | 0.334 | 5.2 | 6.5 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 3.1e-07 | 3.1e-07 | 0.000 | 0.000 | 0.704 | 10.6 | 13.6 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 6.1e-08 | 6.1e-08 | 0.000 | 0.000 | 0.890 | 16.0 | 20.7 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00014 | 0.00014 | 0.002 | 0.009 | 0.245 | 1.5 | 3.7 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 1.4e-05 | 1.4e-05 | 0.000 | 0.002 | 0.453 | 6.5 | 9.7 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 6.4e-06 | 6.4e-06 | 0.000 | 0.002 | 0.692 | 11.9 | 17.7 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 5.9e-06 | 5.9e-06 | 0.000 | 0.002 | 0.809 | 15.9 | 23.7 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 5e-07 | 5e-07 | 0.000 | 0.000 | 0.077 | 1.5 | 3.7 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 2.3e-08 | 2.3e-08 | 0.000 | 0.000 | 0.171 | 5.1 | 7.7 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 2.3e-08 | 2.3e-08 | 0.000 | 0.000 | 0.349 | 9.2 | 13.7 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 2.1e-08 | 2.1e-08 | 0.000 | 0.000 | 0.492 | 13.2 | 19.7 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 7.9e-10 | 7.9e-10 | 0.000 | 0.000 | 0.051 | 3.8 | 5.7 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 3.3e-10 | 3.3e-10 | 0.000 | 0.000 | 0.144 | 7.8 | 11.7 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 3.4e-11 | 3.4e-11 | 0.000 | 0.000 | 0.256 | 11.9 | 17.7 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00339 | 0.0095 | 0.027 | 0.198 | 0.660 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00202 | 0.0097 | 0.044 | 0.369 | 0.743 | 19.9 |
| t | 0 | 0.01 | 30 | 0.00157 | 0.0099 | 0.059 | 0.409 | 0.811 | 29.8 |
| t | 0 | 0.01 | 40 | 0.00129 | 0.01 | 0.067 | 0.436 | 0.861 | 39.8 |
| t | 0 | 0.001 | 10 | 2.5e-04 | 0.0011 | 0.004 | 0.041 | 0.496 | 10.0 |
| t | 0 | 0.001 | 20 | 1.6e-04 | 0.0012 | 0.006 | 0.170 | 0.595 | 20.0 |
| t | 0 | 0.001 | 30 | 1.2e-04 | 0.0011 | 0.008 | 0.219 | 0.682 | 30.0 |
| t | 0 | 0.001 | 40 | 9.0e-05 | 0.0012 | 0.013 | 0.263 | 0.755 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00325 | 0.0041 | 0.010 | 0.056 | 0.567 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.00197 | 0.0038 | 0.010 | 0.121 | 0.634 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.00154 | 0.0031 | 0.010 | 0.157 | 0.702 | 29.9 |
| t | 0.02 | 0.01 | 40 | 0.00137 | 0.0031 | 0.011 | 0.180 | 0.754 | 39.9 |
| t | 0.02 | 0.001 | 10 | 2.6e-04 | 0.00033 | 0.001 | 0.006 | 0.298 | 10.0 |
| t | 0.02 | 0.001 | 20 | 1.7e-04 | 0.00041 | 0.001 | 0.022 | 0.482 | 20.0 |
| t | 0.02 | 0.001 | 30 | 1.0e-04 | 0.00031 | 0.001 | 0.042 | 0.553 | 30.0 |
| t | 0.02 | 0.001 | 40 | 1.0e-04 | 0.00022 | 0.001 | 0.054 | 0.598 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00654 | 0.0087 | 0.042 | 0.369 | 0.611 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00292 | 0.011 | 0.115 | 0.618 | 0.886 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.0022 | 0.01 | 0.177 | 0.784 | 0.968 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 0.00179 | 0.01 | 0.240 | 0.888 | 0.992 | 39.8 |
| wilcoxon | 0 | 0.001 | 10 | 6.9e-04 | 0.00067 | 0.004 | 0.141 | 0.480 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 2.7e-04 | 0.00074 | 0.021 | 0.360 | 0.720 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 2.1e-04 | 0.0012 | 0.046 | 0.556 | 0.896 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 1.6e-04 | 0.0011 | 0.078 | 0.729 | 0.969 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00627 | 0.0017 | 0.009 | 0.095 | 0.583 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00301 | 0.001 | 0.009 | 0.235 | 0.848 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00224 | 0.0007 | 0.010 | 0.361 | 0.953 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.0017 | 0.00066 | 0.010 | 0.468 | 0.986 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 6.0e-04 | 5e-05 | 0.001 | 0.013 | 0.413 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 2.8e-04 | 7e-05 | 0.001 | 0.065 | 0.669 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 1.9e-04 | 4e-05 | 0.001 | 0.133 | 0.859 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 1.4e-04 | 5e-05 | 0.001 | 0.204 | 0.940 | 40.0 |

## Rules under the dev2-gpu-single null (312 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.00062 | 0.00062 | 0.003 | 0.029 | 0.210 | 3.8 | 5.5 |
| 20 | 0.00063 | 0.00063 | 0.003 | 0.034 | 0.315 | 6.6 | 10.2 |
| 30 | 0.00063 | 0.00063 | 0.003 | 0.035 | 0.342 | 7.4 | 12.7 |
| 40 | 0.00063 | 0.00063 | 0.003 | 0.035 | 0.364 | 8.4 | 16.3 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0022 | 0.0022 | 0.006 | 0.012 | 0.032 | 1.7 | 2.0 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0041 | 0.0041 | 0.024 | 0.080 | 0.286 | 7.2 | 10.0 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0054 | 0.0054 | 0.047 | 0.195 | 0.597 | 15.3 | 20.9 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0057 | 0.0057 | 0.065 | 0.285 | 0.757 | 21.3 | 28.3 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0003 | 0.0003 | 0.001 | 0.004 | 0.015 | 1.7 | 2.0 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.00026 | 0.00026 | 0.003 | 0.015 | 0.088 | 5.2 | 7.3 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.00045 | 0.00045 | 0.007 | 0.046 | 0.267 | 11.3 | 16.5 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0005 | 0.0005 | 0.011 | 0.087 | 0.453 | 17.3 | 25.4 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 3e-05 | 3e-05 | 0.000 | 0.002 | 0.020 | 3.4 | 4.4 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 4e-05 | 4e-05 | 0.001 | 0.011 | 0.111 | 9.3 | 13.7 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 4.7e-05 | 4.7e-05 | 0.002 | 0.027 | 0.246 | 15.3 | 23.0 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00055 | 0.00055 | 0.002 | 0.007 | 0.023 | 1.5 | 1.9 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00045 | 0.00045 | 0.004 | 0.034 | 0.183 | 6.1 | 9.0 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.00036 | 0.00036 | 0.005 | 0.073 | 0.417 | 12.9 | 19.1 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.00029 | 0.00029 | 0.006 | 0.103 | 0.569 | 18.0 | 26.5 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 3.5e-05 | 3.5e-05 | 0.000 | 0.002 | 0.009 | 1.5 | 1.9 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 1.3e-05 | 1.3e-05 | 0.000 | 0.004 | 0.046 | 4.5 | 6.5 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 1.7e-05 | 1.7e-05 | 0.000 | 0.012 | 0.146 | 9.5 | 14.4 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 1.5e-05 | 1.5e-05 | 0.000 | 0.020 | 0.264 | 14.6 | 22.3 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 1.3e-06 | 1.3e-06 | 0.000 | 0.001 | 0.009 | 3.0 | 4.1 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 8.2e-07 | 8.2e-07 | 0.000 | 0.002 | 0.049 | 7.8 | 11.9 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 5.4e-07 | 5.4e-07 | 0.000 | 0.004 | 0.115 | 12.9 | 19.8 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 6.1e-05 | 6.1e-05 | 0.000 | 0.002 | 0.012 | 1.2 | 1.7 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 2.4e-05 | 2.4e-05 | 0.000 | 0.004 | 0.080 | 5.3 | 7.2 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 1.2e-05 | 1.2e-05 | 0.000 | 0.005 | 0.195 | 11.1 | 15.3 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 9e-06 | 9e-06 | 0.000 | 0.006 | 0.285 | 15.5 | 21.3 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 1.6e-06 | 1.6e-06 | 0.000 | 0.000 | 0.004 | 1.2 | 1.7 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 2.4e-07 | 2.4e-07 | 0.000 | 0.000 | 0.015 | 3.9 | 5.2 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 2.5e-07 | 2.5e-07 | 0.000 | 0.000 | 0.046 | 8.2 | 11.3 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 2.2e-07 | 2.2e-07 | 0.000 | 0.000 | 0.087 | 12.6 | 17.3 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 1.6e-08 | 1.6e-08 | 0.000 | 0.000 | 0.002 | 2.6 | 3.4 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 6.2e-09 | 6.2e-09 | 0.000 | 0.000 | 0.011 | 6.8 | 9.3 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 2.3e-09 | 2.3e-09 | 0.000 | 0.000 | 0.027 | 11.1 | 15.3 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00387 | 0.01 | 0.020 | 0.049 | 0.236 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00198 | 0.0099 | 0.024 | 0.082 | 0.372 | 19.9 |
| t | 0 | 0.01 | 30 | 0.00149 | 0.01 | 0.028 | 0.107 | 0.469 | 29.8 |
| t | 0 | 0.01 | 40 | 0.00128 | 0.01 | 0.029 | 0.126 | 0.551 | 39.8 |
| t | 0 | 0.001 | 10 | 3.3e-04 | 0.0013 | 0.003 | 0.011 | 0.073 | 10.0 |
| t | 0 | 0.001 | 20 | 1.6e-04 | 0.0011 | 0.004 | 0.020 | 0.173 | 20.0 |
| t | 0 | 0.001 | 30 | 1.0e-04 | 0.0011 | 0.005 | 0.029 | 0.255 | 30.0 |
| t | 0 | 0.001 | 40 | 9.0e-05 | 0.001 | 0.005 | 0.033 | 0.309 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.0039 | 0.0045 | 0.009 | 0.025 | 0.136 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.00196 | 0.0045 | 0.011 | 0.038 | 0.242 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.00154 | 0.0035 | 0.010 | 0.044 | 0.312 | 29.9 |
| t | 0.02 | 0.01 | 40 | 0.00128 | 0.003 | 0.009 | 0.051 | 0.367 | 39.9 |
| t | 0.02 | 0.001 | 10 | 3.0e-04 | 0.00053 | 0.001 | 0.005 | 0.031 | 10.0 |
| t | 0.02 | 0.001 | 20 | 1.3e-04 | 0.00019 | 0.001 | 0.006 | 0.083 | 20.0 |
| t | 0.02 | 0.001 | 30 | 1.3e-04 | 0.00023 | 0.001 | 0.008 | 0.118 | 30.0 |
| t | 0.02 | 0.001 | 40 | 8.0e-05 | 0.00032 | 0.001 | 0.011 | 0.172 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00457 | 0.0093 | 0.020 | 0.043 | 0.170 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00264 | 0.0096 | 0.031 | 0.110 | 0.397 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.0019 | 0.01 | 0.042 | 0.176 | 0.585 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 0.00165 | 0.0093 | 0.046 | 0.221 | 0.697 | 39.8 |
| wilcoxon | 0 | 0.001 | 10 | 7.9e-04 | 0.0009 | 0.003 | 0.009 | 0.036 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 3.0e-04 | 0.00094 | 0.005 | 0.025 | 0.151 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 1.7e-04 | 0.00098 | 0.007 | 0.046 | 0.286 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 1.6e-04 | 0.00092 | 0.009 | 0.075 | 0.434 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00503 | 0.0031 | 0.009 | 0.026 | 0.093 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00269 | 0.0019 | 0.010 | 0.052 | 0.264 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00196 | 0.0019 | 0.010 | 0.073 | 0.403 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.00162 | 0.0014 | 0.010 | 0.090 | 0.516 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 7.7e-04 | 0.00019 | 0.001 | 0.006 | 0.024 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 2.7e-04 | 0.00011 | 0.001 | 0.011 | 0.089 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 2.0e-04 | 0.00011 | 0.001 | 0.013 | 0.152 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 1.5e-04 | 7e-05 | 0.001 | 0.019 | 0.246 | 40.0 |

## Rules under the dev2-gpu-kernels null (277 rounds; m = 3)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=3 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 5.3e-05 | 0.00016 | 0.000 | 0.041 | 0.598 | 3.7 | 5.5 |
| 20 | 5.3e-05 | 0.00016 | 0.000 | 0.045 | 0.746 | 6.0 | 7.4 |
| 30 | 5.3e-05 | 0.00016 | 0.000 | 0.045 | 0.787 | 6.4 | 8.3 |
| 40 | 5.3e-05 | 0.00016 | 0.000 | 0.045 | 0.823 | 6.9 | 9.4 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=3 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0062 | 0.0042 | 0.034 | 0.081 | 0.440 | 2.0 | 3.8 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.006 | 0.0061 | 0.111 | 0.284 | 0.921 | 7.7 | 13.5 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.006 | 0.0054 | 0.179 | 0.455 | 0.991 | 15.3 | 21.4 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0057 | 0.0051 | 0.252 | 0.602 | 0.999 | 21.1 | 27.2 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.00061 | no test at alpha/m | - | - | - | 2.0 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.00035 | 0.00038 | 0.017 | 0.062 | 0.569 | 5.8 | 7.8 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.0005 | 0.00049 | 0.046 | 0.178 | 0.919 | 11.6 | 18.5 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.00048 | 0.00042 | 0.097 | 0.362 | 0.994 | 17.3 | 30.3 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 4.5e-05 | 4.1e-05 | 0.006 | 0.030 | 0.480 | 3.9 | 8.0 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 4.3e-05 | 3.8e-05 | 0.013 | 0.071 | 0.788 | 9.6 | 15.8 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 3.7e-05 | 3.9e-05 | 0.026 | 0.151 | 0.957 | 15.4 | 26.6 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 9e-05 | 1.8e-05 | 0.001 | 0.050 | 0.309 | 1.4 | 3.4 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 2.4e-05 | 6.7e-06 | 0.002 | 0.173 | 0.801 | 5.4 | 12.6 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 8.8e-06 | 4.7e-06 | 0.002 | 0.283 | 0.951 | 10.9 | 21.0 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 7.1e-06 | 1.9e-06 | 0.002 | 0.394 | 0.989 | 14.9 | 28.0 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 1.4e-06 | no test at alpha/m | - | - | - | 1.4 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 1.1e-07 | 9.5e-08 | 0.000 | 0.031 | 0.380 | 4.1 | 6.9 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 1.1e-07 | 8.7e-08 | 0.000 | 0.087 | 0.769 | 8.1 | 16.8 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 1.1e-07 | 2.2e-08 | 0.000 | 0.186 | 0.956 | 12.2 | 29.0 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 6.4e-09 | 1.5e-09 | 0.000 | 0.013 | 0.287 | 2.7 | 7.0 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 2e-09 | 4.7e-10 | 0.000 | 0.029 | 0.563 | 6.8 | 13.9 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 5.2e-10 | 4e-10 | 0.000 | 0.061 | 0.825 | 10.9 | 24.0 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 1.3e-05 | 1.5e-06 | 0.000 | 0.001 | 0.089 | 1.3 | 2.0 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 2.4e-06 | 3.6e-07 | 0.000 | 0.002 | 0.311 | 5.0 | 7.7 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 6.3e-07 | 2.8e-07 | 0.000 | 0.002 | 0.494 | 10.0 | 13.5 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 5.3e-07 | 7.7e-08 | 0.000 | 0.002 | 0.645 | 13.7 | 19.2 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 8.8e-08 | no test at alpha/m | - | - | - | 1.3 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 3.8e-09 | 2.4e-09 | 0.000 | 0.000 | 0.071 | 3.8 | 3.9 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 3.8e-09 | 2.3e-09 | 0.000 | 0.000 | 0.203 | 7.5 | 9.6 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 3.7e-09 | 4.4e-10 | 0.000 | 0.000 | 0.406 | 11.2 | 17.3 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 1.4e-10 | 1.7e-11 | 0.000 | 0.000 | 0.035 | 2.5 | 3.9 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 3e-11 | 3.8e-12 | 0.000 | 0.000 | 0.084 | 6.2 | 7.7 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 5.7e-12 | 3.5e-12 | 0.000 | 0.000 | 0.178 | 10.0 | 13.5 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=3 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 9.9e-04 | 0.011 | 0.054 | 0.283 | 0.715 | 10.0 |
| t | 0 | 0.01 | 20 | 5.6e-04 | 0.01 | 0.070 | 0.441 | 0.935 | 20.0 |
| t | 0 | 0.01 | 30 | 3.9e-04 | 0.0093 | 0.085 | 0.575 | 0.992 | 29.9 |
| t | 0 | 0.01 | 40 | 3.5e-04 | 0.0084 | 0.098 | 0.684 | 0.999 | 39.9 |
| t | 0.02 | 0.01 | 10 | 9.1e-04 | 0.00096 | 0.003 | 0.112 | 0.586 | 10.0 |
| t | 0.02 | 0.01 | 20 | 5.5e-04 | 0.00084 | 0.003 | 0.165 | 0.812 | 20.0 |
| t | 0.02 | 0.01 | 30 | 3.8e-04 | 0.0006 | 0.003 | 0.222 | 0.939 | 30.0 |
| t | 0.02 | 0.01 | 40 | 3.5e-04 | 0.00057 | 0.003 | 0.271 | 0.984 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00225 | 0.0091 | 0.054 | 0.179 | 0.584 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00102 | 0.0095 | 0.078 | 0.454 | 0.882 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 6.1e-04 | 0.0099 | 0.121 | 0.677 | 0.983 | 30.0 |
| wilcoxon | 0 | 0.01 | 40 | 4.9e-04 | 0.01 | 0.157 | 0.832 | 0.998 | 39.9 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00227 | 3e-05 | 0.003 | 0.085 | 0.471 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 9.7e-04 | 3e-05 | 0.004 | 0.163 | 0.774 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 6.6e-04 | 3e-05 | 0.003 | 0.263 | 0.938 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 5.0e-04 | <1e-12 | 0.003 | 0.343 | 0.985 | 40.0 |

## Rules under the dev3-joint null (309 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.0041 | 0.0041 | 0.016 | 0.075 | 0.339 | 5.7 | 6.0 |
| 20 | 0.0041 | 0.0041 | 0.017 | 0.083 | 0.424 | 10.2 | 9.9 |
| 30 | 0.0041 | 0.0041 | 0.017 | 0.083 | 0.445 | 12.9 | 12.2 |
| 40 | 0.0041 | 0.0041 | 0.017 | 0.083 | 0.462 | 16.9 | 15.7 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.009 | 0.021 | 2.0 | 2.2 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0026 | 0.0026 | 0.012 | 0.059 | 0.315 | 9.0 | 11.3 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0052 | 0.0052 | 0.031 | 0.157 | 0.682 | 17.8 | 22.2 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0066 | 0.0066 | 0.048 | 0.243 | 0.847 | 24.4 | 29.7 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.001 | 0.007 | 2.0 | 2.2 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.00011 | 0.00011 | 0.001 | 0.008 | 0.095 | 6.9 | 8.6 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.00027 | 0.00027 | 0.003 | 0.028 | 0.313 | 13.4 | 17.6 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.00031 | 0.00031 | 0.005 | 0.051 | 0.523 | 20.0 | 26.5 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 3.9e-06 | 3.9e-06 | 0.000 | 0.001 | 0.017 | 4.6 | 5.5 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.2e-05 | 1.2e-05 | 0.000 | 0.004 | 0.112 | 11.3 | 14.7 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 1.8e-05 | 1.8e-05 | 0.000 | 0.010 | 0.271 | 17.8 | 23.8 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.017 | 2.0 | 2.0 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00017 | 0.00017 | 0.003 | 0.018 | 0.212 | 8.2 | 10.4 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0002 | 0.0002 | 0.005 | 0.053 | 0.514 | 15.8 | 20.9 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.00019 | 0.00019 | 0.007 | 0.086 | 0.697 | 21.4 | 28.6 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.005 | 2.0 | 2.0 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 2.6e-06 | 2.6e-06 | 0.000 | 0.002 | 0.052 | 6.3 | 7.7 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 4.3e-06 | 4.3e-06 | 0.000 | 0.006 | 0.182 | 12.0 | 15.9 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 3e-06 | 3e-06 | 0.000 | 0.010 | 0.330 | 17.7 | 24.0 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 5.2e-08 | 5.2e-08 | 0.000 | 0.000 | 0.008 | 4.3 | 4.9 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 7.5e-08 | 7.5e-08 | 0.000 | 0.000 | 0.052 | 10.1 | 13.2 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 5.9e-08 | 5.9e-08 | 0.000 | 0.001 | 0.133 | 15.8 | 21.4 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.010 | 2.0 | 2.0 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 5.6e-06 | 5.6e-06 | 0.000 | 0.003 | 0.071 | 7.5 | 9.0 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 3.9e-06 | 3.9e-06 | 0.000 | 0.005 | 0.187 | 14.0 | 17.8 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 2.6e-06 | 2.6e-06 | 0.000 | 0.007 | 0.286 | 18.9 | 24.4 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.002 | 2.0 | 2.0 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 2.6e-08 | 2.6e-08 | 0.000 | 0.000 | 0.011 | 5.9 | 6.9 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 3.2e-08 | 3.2e-08 | 0.000 | 0.000 | 0.036 | 10.7 | 13.4 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 1.4e-08 | 1.4e-08 | 0.000 | 0.000 | 0.067 | 15.6 | 20.0 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 2.9e-10 | 2.9e-10 | 0.000 | 0.000 | 0.001 | 4.1 | 4.6 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.6e-10 | 1.6e-10 | 0.000 | 0.000 | 0.006 | 9.1 | 11.3 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 7.4e-11 | 7.4e-11 | 0.000 | 0.000 | 0.015 | 14.0 | 17.8 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00369 | 0.0097 | 0.027 | 0.098 | 0.510 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00202 | 0.0097 | 0.043 | 0.243 | 0.899 | 19.9 |
| t | 0 | 0.01 | 30 | 0.00148 | 0.01 | 0.059 | 0.398 | 0.985 | 29.8 |
| t | 0 | 0.01 | 40 | 0.00132 | 0.01 | 0.072 | 0.524 | 0.998 | 39.8 |
| t | 0 | 0.001 | 10 | 2.7e-04 | 0.0011 | 0.005 | 0.023 | 0.141 | 10.0 |
| t | 0 | 0.001 | 20 | 1.4e-04 | 0.0013 | 0.007 | 0.055 | 0.558 | 20.0 |
| t | 0 | 0.001 | 30 | 1.1e-04 | 0.0009 | 0.009 | 0.128 | 0.884 | 30.0 |
| t | 0 | 0.001 | 40 | 1.0e-04 | 0.00097 | 0.013 | 0.225 | 0.977 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00364 | 0.0024 | 0.011 | 0.044 | 0.307 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.00215 | 0.0016 | 0.010 | 0.082 | 0.691 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.0016 | 0.0014 | 0.010 | 0.127 | 0.891 | 30.0 |
| t | 0.02 | 0.01 | 40 | 0.00123 | 0.00094 | 0.010 | 0.181 | 0.971 | 40.0 |
| t | 0.02 | 0.001 | 10 | 2.7e-04 | 7e-05 | 0.001 | 0.009 | 0.071 | 10.0 |
| t | 0.02 | 0.001 | 20 | 1.4e-04 | 0.00011 | 0.001 | 0.015 | 0.315 | 20.0 |
| t | 0.02 | 0.001 | 30 | 1.1e-04 | 8e-05 | 0.001 | 0.030 | 0.629 | 30.0 |
| t | 0.02 | 0.001 | 40 | 9.0e-05 | 0.0001 | 0.001 | 0.042 | 0.823 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00424 | 0.0098 | 0.028 | 0.096 | 0.436 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00253 | 0.0095 | 0.043 | 0.229 | 0.842 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.00176 | 0.01 | 0.057 | 0.355 | 0.969 | 29.8 |
| wilcoxon | 0 | 0.01 | 40 | 0.00147 | 0.0096 | 0.073 | 0.496 | 0.996 | 39.8 |
| wilcoxon | 0 | 0.001 | 10 | 4.8e-04 | 0.00091 | 0.005 | 0.033 | 0.149 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 2.3e-04 | 0.0011 | 0.007 | 0.069 | 0.510 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 1.6e-04 | 0.00095 | 0.010 | 0.129 | 0.823 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 1.2e-04 | 0.0013 | 0.016 | 0.236 | 0.966 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00443 | 0.0016 | 0.008 | 0.039 | 0.291 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00257 | 0.0011 | 0.010 | 0.088 | 0.644 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00177 | 0.001 | 0.010 | 0.122 | 0.838 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.00154 | 0.00081 | 0.010 | 0.182 | 0.951 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 3.5e-04 | 5e-05 | 0.001 | 0.008 | 0.062 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 2.1e-04 | 2e-05 | 0.001 | 0.017 | 0.304 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 1.7e-04 | 8e-05 | 0.001 | 0.032 | 0.587 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 1.3e-04 | 4e-05 | 0.001 | 0.046 | 0.777 | 40.0 |

## Rules under the dev3-gpu-single null (387 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.0019 | 0.0019 | 0.012 | 0.089 | 0.658 | 4.8 | 5.5 |
| 20 | 0.0019 | 0.0019 | 0.012 | 0.101 | 0.807 | 7.7 | 7.2 |
| 30 | 0.0019 | 0.0019 | 0.012 | 0.102 | 0.847 | 8.9 | 7.9 |
| 40 | 0.0019 | 0.0019 | 0.012 | 0.102 | 0.882 | 10.6 | 8.7 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.016 | 0.016 | 0.044 | 0.178 | 0.460 | 2.3 | 3.7 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.018 | 0.018 | 0.080 | 0.467 | 0.966 | 8.7 | 12.7 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.021 | 0.021 | 0.128 | 0.735 | 1.000 | 17.0 | 19.8 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.022 | 0.022 | 0.161 | 0.853 | 1.000 | 23.1 | 23.0 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0021 | 0.0021 | 0.010 | 0.080 | 0.389 | 2.4 | 4.2 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.0015 | 0.0015 | 0.013 | 0.198 | 0.851 | 6.7 | 12.0 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.0024 | 0.0024 | 0.027 | 0.417 | 0.991 | 13.0 | 21.1 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0026 | 0.0026 | 0.038 | 0.594 | 1.000 | 19.3 | 28.1 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.00023 | 0.00023 | 0.003 | 0.067 | 0.600 | 4.6 | 8.6 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.00027 | 0.00027 | 0.006 | 0.208 | 0.959 | 10.9 | 20.4 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.00029 | 0.00029 | 0.009 | 0.370 | 0.997 | 17.2 | 30.1 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0045 | 0.0045 | 0.016 | 0.072 | 0.356 | 2.1 | 3.0 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0024 | 0.0024 | 0.018 | 0.157 | 0.861 | 7.5 | 11.2 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0016 | 0.0016 | 0.021 | 0.270 | 0.988 | 14.1 | 21.0 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0013 | 0.0013 | 0.022 | 0.349 | 0.998 | 19.1 | 27.6 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.00024 | 0.00024 | 0.002 | 0.020 | 0.249 | 2.1 | 3.1 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 6.7e-05 | 6.7e-05 | 0.002 | 0.036 | 0.627 | 5.8 | 9.2 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 7.6e-05 | 7.6e-05 | 0.002 | 0.079 | 0.912 | 10.8 | 17.8 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 6.7e-05 | 6.7e-05 | 0.003 | 0.119 | 0.983 | 15.8 | 26.2 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 7.1e-06 | 7.1e-06 | 0.000 | 0.008 | 0.345 | 4.1 | 6.3 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 4e-06 | 4e-06 | 0.000 | 0.021 | 0.770 | 9.1 | 15.4 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 2.1e-06 | 2.1e-06 | 0.000 | 0.039 | 0.939 | 14.1 | 24.3 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00053 | 0.00053 | 0.003 | 0.016 | 0.178 | 1.8 | 2.3 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00014 | 0.00014 | 0.001 | 0.018 | 0.467 | 6.3 | 8.7 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 5.1e-05 | 5.1e-05 | 0.001 | 0.021 | 0.735 | 11.8 | 17.0 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 4.2e-05 | 4.2e-05 | 0.001 | 0.022 | 0.853 | 15.9 | 23.1 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | 8.6e-06 | 8.6e-06 | 0.000 | 0.002 | 0.080 | 1.8 | 2.4 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 7.3e-07 | 7.3e-07 | 0.000 | 0.002 | 0.198 | 5.0 | 6.7 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 7.4e-07 | 7.4e-07 | 0.000 | 0.002 | 0.417 | 9.1 | 13.0 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 7e-07 | 7e-07 | 0.000 | 0.003 | 0.594 | 13.2 | 19.3 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 4.4e-08 | 4.4e-08 | 0.000 | 0.000 | 0.067 | 3.5 | 4.6 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.4e-08 | 1.4e-08 | 0.000 | 0.000 | 0.208 | 7.7 | 10.9 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 3.7e-09 | 3.7e-09 | 0.000 | 0.000 | 0.370 | 11.8 | 17.2 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00341 | 0.01 | 0.032 | 0.128 | 0.528 | 10.0 |
| t | 0 | 0.01 | 20 | 0.0019 | 0.0098 | 0.054 | 0.355 | 0.947 | 19.9 |
| t | 0 | 0.01 | 30 | 0.00152 | 0.01 | 0.083 | 0.596 | 0.997 | 29.8 |
| t | 0 | 0.01 | 40 | 0.00124 | 0.0097 | 0.112 | 0.776 | 1.000 | 39.8 |
| t | 0 | 0.001 | 10 | 2.5e-04 | 0.00092 | 0.004 | 0.026 | 0.187 | 10.0 |
| t | 0 | 0.001 | 20 | 1.4e-04 | 0.0013 | 0.009 | 0.111 | 0.741 | 20.0 |
| t | 0 | 0.001 | 30 | 1.2e-04 | 0.00096 | 0.015 | 0.290 | 0.977 | 30.0 |
| t | 0 | 0.001 | 40 | 1.0e-04 | 0.0011 | 0.025 | 0.522 | 0.999 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00351 | 0.0031 | 0.010 | 0.052 | 0.340 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.00192 | 0.0017 | 0.009 | 0.112 | 0.809 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.0015 | 0.0014 | 0.010 | 0.207 | 0.970 | 30.0 |
| t | 0.02 | 0.01 | 40 | 0.00135 | 0.0015 | 0.010 | 0.302 | 0.997 | 40.0 |
| t | 0.02 | 0.001 | 10 | 3.1e-04 | 0.00033 | 0.001 | 0.008 | 0.102 | 10.0 |
| t | 0.02 | 0.001 | 20 | 1.3e-04 | 0.00021 | 0.001 | 0.026 | 0.536 | 20.0 |
| t | 0.02 | 0.001 | 30 | 1.1e-04 | 0.00013 | 0.001 | 0.042 | 0.818 | 30.0 |
| t | 0.02 | 0.001 | 40 | 9.0e-05 | 8e-05 | 0.001 | 0.083 | 0.963 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00691 | 0.01 | 0.039 | 0.192 | 0.598 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.0032 | 0.0096 | 0.071 | 0.460 | 0.966 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.00219 | 0.011 | 0.106 | 0.707 | 0.999 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 0.00172 | 0.0091 | 0.144 | 0.868 | 1.000 | 39.8 |
| wilcoxon | 0 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 3.2e-04 | 0.00078 | 0.011 | 0.178 | 0.790 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 2.2e-04 | 0.001 | 0.025 | 0.429 | 0.990 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 1.6e-04 | 0.001 | 0.034 | 0.620 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00615 | 0.0011 | 0.008 | 0.060 | 0.437 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00332 | 0.00068 | 0.010 | 0.159 | 0.880 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00215 | 0.00049 | 0.010 | 0.261 | 0.990 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.00191 | 0.00051 | 0.009 | 0.381 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 0 | <1e-12 | 0.000 | 0.000 | 0.000 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 3.5e-04 | 2e-05 | 0.001 | 0.044 | 0.658 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 2.2e-04 | 3e-05 | 0.001 | 0.084 | 0.936 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 1.4e-04 | 1e-05 | 0.001 | 0.148 | 0.995 | 40.0 |

## Rules under the dev3-gpu-kernels null (320 rounds; m = 3)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=3 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | <1e-12 | <1e-12 | 0.000 | 0.083 | 1.000 | 3.0 | 5.0 |
| 20 | <1e-12 | <1e-12 | 0.000 | 0.099 | 1.000 | 5.0 | 5.0 |
| 30 | <1e-12 | <1e-12 | 0.000 | 0.100 | 1.000 | 5.0 | 5.0 |
| 40 | <1e-12 | <1e-12 | 0.000 | 0.100 | 1.000 | 5.0 | 5.0 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=3 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.013 | 0.011 | 0.706 | 0.933 | 0.966 | 2.1 | 8.7 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.02 | 0.024 | 0.995 | 1.000 | 1.000 | 8.6 | 10.2 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.025 | 0.027 | 1.000 | 1.000 | 1.000 | 17.2 | 10.3 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.027 | 0.032 | 1.000 | 1.000 | 1.000 | 23.6 | 11.3 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0021 | no test at alpha/m | - | - | - | 2.1 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.0018 | 0.0018 | 0.871 | 0.994 | 0.998 | 6.5 | 13.3 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.0031 | 0.0032 | 0.997 | 1.000 | 1.000 | 13.0 | 13.5 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0036 | 0.0044 | 1.000 | 1.000 | 1.000 | 19.6 | 14.4 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 0.00028 | 0.00035 | 0.832 | 0.992 | 0.998 | 4.3 | 16.4 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.00038 | 0.00041 | 0.981 | 1.000 | 1.000 | 10.9 | 17.5 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.00048 | 0.00053 | 1.000 | 1.000 | 1.000 | 17.4 | 17.6 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 4.3e-10 | 3e-12 | 0.004 | 0.901 | 0.966 | 1.0 | 8.6 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 2.9e-11 | <1e-12 | 0.008 | 1.000 | 1.000 | 4.2 | 10.3 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 1e-12 | <1e-12 | 0.009 | 1.000 | 1.000 | 8.4 | 10.4 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 1e-12 | <1e-12 | 0.011 | 1.000 | 1.000 | 11.6 | 11.4 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | no test at alpha/m | - | - | - | 1.0 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.001 | 0.987 | 0.998 | 3.1 | 13.5 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.001 | 1.000 | 1.000 | 6.3 | 13.7 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.001 | 1.000 | 1.000 | 9.5 | 14.6 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.983 | 0.998 | 2.1 | 16.5 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 5.3 | 17.8 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 8.4 | 17.9 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.004 | 0.966 | 1.0 | 2.1 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | <1e-12 | <1e-12 | 0.000 | 0.008 | 1.000 | 4.0 | 8.6 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.000 | 0.009 | 1.000 | 8.1 | 15.2 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.000 | 0.011 | 1.000 | 11.1 | 21.7 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | no test at alpha/m | - | - | - | 1.0 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.001 | 0.998 | 3.0 | 4.3 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.001 | 1.000 | 6.0 | 10.9 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.001 | 1.000 | 9.1 | 19.6 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.998 | 2.0 | 4.3 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 5.0 | 8.7 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 8.1 | 15.2 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=3 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 9.4e-04 | 0.01 | 0.845 | 0.979 | 1.000 | 10.0 |
| t | 0 | 0.01 | 20 | 4.6e-04 | 0.0095 | 0.956 | 1.000 | 1.000 | 20.0 |
| t | 0 | 0.01 | 30 | 4.0e-04 | 0.0086 | 0.986 | 1.000 | 1.000 | 30.0 |
| t | 0 | 0.01 | 40 | 3.3e-04 | 0.011 | 0.998 | 1.000 | 1.000 | 39.9 |
| t | 0.02 | 0.01 | 10 | 9.6e-04 | <1e-12 | 0.003 | 0.951 | 1.000 | 10.0 |
| t | 0.02 | 0.01 | 20 | 4.8e-04 | <1e-12 | 0.003 | 0.993 | 1.000 | 20.0 |
| t | 0.02 | 0.01 | 30 | 3.6e-04 | <1e-12 | 0.004 | 1.000 | 1.000 | 30.0 |
| t | 0.02 | 0.01 | 40 | 3.1e-04 | <1e-12 | 0.003 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00299 | 0.0094 | 0.632 | 0.836 | 0.864 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 9.7e-04 | 0.01 | 0.978 | 0.998 | 1.000 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 6.7e-04 | 0.01 | 0.999 | 1.000 | 1.000 | 30.0 |
| wilcoxon | 0 | 0.01 | 40 | 5.4e-04 | 0.012 | 1.000 | 1.000 | 1.000 | 39.9 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00278 | <1e-12 | 0.003 | 0.806 | 0.863 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 9.5e-04 | <1e-12 | 0.003 | 0.996 | 1.000 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 7.1e-04 | <1e-12 | 0.003 | 1.000 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 5.1e-04 | <1e-12 | 0.003 | 1.000 | 1.000 | 40.0 |

## Rules under the dev4-joint null (288 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 5.1e-09 | 5.1e-09 | 0.000 | 0.037 | 0.993 | 3.2 | 5.0 |
| 20 | 5.1e-09 | 5.1e-09 | 0.000 | 0.037 | 1.000 | 5.2 | 5.0 |
| 30 | 5.1e-09 | 5.1e-09 | 0.000 | 0.037 | 1.000 | 5.2 | 5.0 |
| 40 | 5.1e-09 | 5.1e-09 | 0.000 | 0.037 | 1.000 | 5.2 | 5.0 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0014 | 0.0014 | 0.040 | 0.643 | 0.959 | 1.9 | 6.2 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.00022 | 0.00022 | 0.027 | 0.957 | 1.000 | 8.3 | 10.8 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0002 | 0.0002 | 0.042 | 0.999 | 1.000 | 16.5 | 11.9 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.00019 | 0.00019 | 0.053 | 1.000 | 1.000 | 22.6 | 12.3 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 9.3e-06 | 9.3e-06 | 0.002 | 0.414 | 0.919 | 1.9 | 7.9 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 1.8e-06 | 1.8e-06 | 0.002 | 0.804 | 1.000 | 6.3 | 15.0 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 2.1e-06 | 2.1e-06 | 0.003 | 0.974 | 1.000 | 12.4 | 17.1 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 1.4e-06 | 1.4e-06 | 0.004 | 0.997 | 1.000 | 18.5 | 17.8 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 7.9e-08 | 7.9e-08 | 0.000 | 0.520 | 0.989 | 4.2 | 14.5 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 6.6e-08 | 6.6e-08 | 0.000 | 0.889 | 1.000 | 10.4 | 21.5 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 1.1e-08 | 1.1e-08 | 0.000 | 0.982 | 1.000 | 16.5 | 23.7 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 5.1e-06 | 5.1e-06 | 0.001 | 0.165 | 0.938 | 1.1 | 4.7 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 1.9e-07 | 1.9e-07 | 0.000 | 0.268 | 1.000 | 6.1 | 13.3 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 1.2e-07 | 1.2e-07 | 0.000 | 0.471 | 1.000 | 12.4 | 22.1 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 1.2e-07 | 1.2e-07 | 0.000 | 0.605 | 1.000 | 17.1 | 27.2 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 3.5e-09 | 3.5e-09 | 0.000 | 0.031 | 0.881 | 1.1 | 5.0 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 9.8e-11 | 9.8e-11 | 0.000 | 0.068 | 0.999 | 4.5 | 11.7 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 9.8e-11 | 9.8e-11 | 0.000 | 0.155 | 1.000 | 9.2 | 21.0 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 8.4e-11 | 8.4e-11 | 0.000 | 0.237 | 1.000 | 14.0 | 29.7 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 1.8e-12 | 1.8e-12 | 0.000 | 0.014 | 0.977 | 2.9 | 8.5 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 1.2e-12 | 1.2e-12 | 0.000 | 0.041 | 1.000 | 7.7 | 18.7 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.078 | 1.000 | 12.4 | 28.6 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.001 | 0.712 | 1.0 | 1.9 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.981 | 4.3 | 8.3 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 8.8 | 16.5 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 12.2 | 22.6 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.507 | 1.0 | 1.9 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.886 | 3.2 | 6.3 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.992 | 6.5 | 12.4 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.999 | 9.9 | 18.5 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.646 | 2.1 | 4.2 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.953 | 5.5 | 10.4 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.996 | 8.8 | 16.5 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00294 | 0.0096 | 0.458 | 0.974 | 1.000 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00176 | 0.01 | 0.774 | 0.997 | 1.000 | 19.9 |
| t | 0 | 0.01 | 30 | 0.0014 | 0.01 | 0.870 | 1.000 | 1.000 | 29.8 |
| t | 0 | 0.01 | 40 | 0.00121 | 0.01 | 0.914 | 1.000 | 1.000 | 39.8 |
| t | 0 | 0.001 | 10 | 2.5e-04 | 0.00077 | 0.138 | 0.948 | 0.994 | 10.0 |
| t | 0 | 0.001 | 20 | 1.3e-04 | 0.00099 | 0.480 | 0.979 | 1.000 | 20.0 |
| t | 0 | 0.001 | 30 | 1.1e-04 | 0.00095 | 0.701 | 0.998 | 1.000 | 30.0 |
| t | 0 | 0.001 | 40 | 9.0e-05 | 0.00099 | 0.816 | 1.000 | 1.000 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00303 | 1e-05 | 0.010 | 0.866 | 0.995 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.00173 | 1e-05 | 0.010 | 0.954 | 1.000 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.00137 | <1e-12 | 0.011 | 0.979 | 1.000 | 30.0 |
| t | 0.02 | 0.01 | 40 | 0.00119 | 1e-05 | 0.010 | 0.992 | 1.000 | 40.0 |
| t | 0.02 | 0.001 | 10 | 2.7e-04 | 1e-05 | 0.001 | 0.588 | 0.986 | 10.0 |
| t | 0.02 | 0.001 | 20 | 1.3e-04 | <1e-12 | 0.001 | 0.895 | 1.000 | 20.0 |
| t | 0.02 | 0.001 | 30 | 1.0e-04 | 1e-05 | 0.001 | 0.939 | 1.000 | 30.0 |
| t | 0.02 | 0.001 | 40 | 8.0e-05 | <1e-12 | 0.001 | 0.973 | 1.000 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00557 | 0.0091 | 0.449 | 0.986 | 0.999 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00286 | 0.0099 | 0.800 | 1.000 | 1.000 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.00192 | 0.01 | 0.941 | 1.000 | 1.000 | 29.8 |
| wilcoxon | 0 | 0.01 | 40 | 0.00155 | 0.0099 | 0.986 | 1.000 | 1.000 | 39.8 |
| wilcoxon | 0 | 0.001 | 10 | 6.1e-04 | 0.0011 | 0.150 | 0.927 | 0.968 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 2.6e-04 | 0.001 | 0.459 | 0.999 | 1.000 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 1.7e-04 | 0.00092 | 0.717 | 1.000 | 1.000 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 1.3e-04 | 0.0008 | 0.920 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00535 | <1e-12 | 0.010 | 0.820 | 0.997 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00267 | <1e-12 | 0.010 | 0.989 | 1.000 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00197 | <1e-12 | 0.011 | 0.999 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.00154 | <1e-12 | 0.009 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 6.3e-04 | <1e-12 | 0.001 | 0.538 | 0.968 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 2.7e-04 | <1e-12 | 0.001 | 0.928 | 1.000 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 1.9e-04 | <1e-12 | 0.001 | 0.995 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 1.4e-04 | <1e-12 | 0.001 | 1.000 | 1.000 | 40.0 |

## Rules under the dev4-gpu-single null (476 rounds; m = 1)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | 0.00091 | 0.00091 | 0.007 | 0.081 | 0.340 | 5.8 | 5.7 |
| 20 | 0.00091 | 0.00091 | 0.007 | 0.086 | 0.384 | 10.7 | 9.0 |
| 30 | 0.00091 | 0.00091 | 0.007 | 0.086 | 0.393 | 13.9 | 11.1 |
| 40 | 0.00091 | 0.00091 | 0.007 | 0.086 | 0.398 | 18.5 | 14.3 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0027 | 0.0027 | 0.010 | 0.032 | 0.104 | 2.2 | 2.9 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0022 | 0.0022 | 0.013 | 0.046 | 0.164 | 9.3 | 11.3 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.0035 | 0.0035 | 0.029 | 0.098 | 0.313 | 18.4 | 22.0 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.0044 | 0.0044 | 0.043 | 0.145 | 0.428 | 25.3 | 29.6 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 8.5e-05 | 8.5e-05 | 0.001 | 0.003 | 0.016 | 2.2 | 3.0 |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 7.9e-05 | 7.9e-05 | 0.001 | 0.006 | 0.033 | 7.0 | 8.7 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.00015 | 0.00015 | 0.002 | 0.013 | 0.078 | 13.9 | 17.2 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.00015 | 0.00015 | 0.003 | 0.021 | 0.123 | 20.8 | 25.7 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 5.1e-06 | 5.1e-06 | 0.000 | 0.001 | 0.006 | 4.6 | 5.9 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 7e-06 | 7e-06 | 0.000 | 0.002 | 0.016 | 11.6 | 14.5 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 5.8e-06 | 5.8e-06 | 0.000 | 0.003 | 0.031 | 18.5 | 23.0 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | 0.00026 | 0.00026 | 0.003 | 0.012 | 0.068 | 2.1 | 2.4 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | 8.8e-05 | 8.8e-05 | 0.002 | 0.021 | 0.096 | 8.3 | 10.6 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | 9.1e-05 | 9.1e-05 | 0.004 | 0.048 | 0.187 | 16.3 | 21.2 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | 8.4e-05 | 8.4e-05 | 0.004 | 0.075 | 0.265 | 22.3 | 29.0 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | 2.5e-06 | 2.5e-06 | 0.000 | 0.001 | 0.008 | 2.1 | 2.4 |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | 9.3e-07 | 9.3e-07 | 0.000 | 0.002 | 0.015 | 6.4 | 7.9 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | 1.2e-06 | 1.2e-06 | 0.000 | 0.005 | 0.035 | 12.3 | 16.2 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | 8e-07 | 8e-07 | 0.000 | 0.008 | 0.053 | 18.3 | 24.4 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 3.4e-08 | 3.4e-08 | 0.000 | 0.000 | 0.002 | 4.3 | 5.2 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 3e-08 | 3e-08 | 0.000 | 0.000 | 0.005 | 10.3 | 13.4 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 8.9e-09 | 8.9e-09 | 0.000 | 0.001 | 0.010 | 16.3 | 21.7 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.003 | 0.034 | 2.0 | 2.2 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | 7.4e-08 | 7.4e-08 | 0.000 | 0.002 | 0.052 | 7.5 | 9.3 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | 3.4e-08 | 3.4e-08 | 0.000 | 0.004 | 0.111 | 14.3 | 18.4 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | 2.2e-08 | 2.2e-08 | 0.000 | 0.004 | 0.165 | 19.4 | 25.3 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.003 | 2.0 | 2.2 |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | 6.5e-11 | 6.5e-11 | 0.000 | 0.000 | 0.007 | 5.9 | 7.0 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | 7e-11 | 7e-11 | 0.000 | 0.000 | 0.016 | 10.9 | 13.9 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | 2e-11 | 2e-11 | 0.000 | 0.000 | 0.025 | 16.0 | 20.8 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.001 | 4.1 | 4.6 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.002 | 9.2 | 11.6 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 0.004 | 14.3 | 18.5 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=1 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 0.00295 | 0.01 | 0.036 | 0.140 | 0.505 | 10.0 |
| t | 0 | 0.01 | 20 | 0.00159 | 0.0097 | 0.044 | 0.215 | 0.754 | 19.9 |
| t | 0 | 0.01 | 30 | 0.0013 | 0.01 | 0.052 | 0.296 | 0.893 | 29.8 |
| t | 0 | 0.01 | 40 | 0.00114 | 0.01 | 0.061 | 0.383 | 0.960 | 39.8 |
| t | 0 | 0.001 | 10 | 2.6e-04 | 0.0012 | 0.007 | 0.043 | 0.268 | 10.0 |
| t | 0 | 0.001 | 20 | 1.3e-04 | 0.0012 | 0.007 | 0.057 | 0.446 | 20.0 |
| t | 0 | 0.001 | 30 | 9.0e-05 | 0.00099 | 0.008 | 0.090 | 0.668 | 30.0 |
| t | 0 | 0.001 | 40 | 7.0e-05 | 0.00082 | 0.011 | 0.153 | 0.857 | 40.0 |
| t | 0.02 | 0.01 | 10 | 0.00293 | 0.0019 | 0.010 | 0.060 | 0.339 | 10.0 |
| t | 0.02 | 0.01 | 20 | 0.00161 | 0.0016 | 0.010 | 0.081 | 0.554 | 20.0 |
| t | 0.02 | 0.01 | 30 | 0.00129 | 0.0013 | 0.010 | 0.106 | 0.722 | 30.0 |
| t | 0.02 | 0.01 | 40 | 0.00104 | 0.001 | 0.009 | 0.133 | 0.840 | 40.0 |
| t | 0.02 | 0.001 | 10 | 2.4e-04 | 0.00015 | 0.001 | 0.014 | 0.150 | 10.0 |
| t | 0.02 | 0.001 | 20 | 1.3e-04 | 0.0001 | 0.001 | 0.014 | 0.255 | 20.0 |
| t | 0.02 | 0.001 | 30 | 9.0e-05 | 0.00013 | 0.001 | 0.021 | 0.418 | 30.0 |
| t | 0.02 | 0.001 | 40 | 8.0e-05 | 7e-05 | 0.001 | 0.033 | 0.638 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00513 | 0.009 | 0.031 | 0.105 | 0.379 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 0.00275 | 0.011 | 0.045 | 0.192 | 0.729 | 19.9 |
| wilcoxon | 0 | 0.01 | 30 | 0.00201 | 0.01 | 0.055 | 0.275 | 0.906 | 29.9 |
| wilcoxon | 0 | 0.01 | 40 | 0.00163 | 0.0095 | 0.060 | 0.363 | 0.973 | 39.8 |
| wilcoxon | 0 | 0.001 | 10 | 6.6e-04 | 0.00089 | 0.005 | 0.023 | 0.133 | 10.0 |
| wilcoxon | 0 | 0.001 | 20 | 3.2e-04 | 0.001 | 0.007 | 0.046 | 0.389 | 20.0 |
| wilcoxon | 0 | 0.001 | 30 | 1.8e-04 | 0.0012 | 0.010 | 0.087 | 0.696 | 30.0 |
| wilcoxon | 0 | 0.001 | 40 | 1.4e-04 | 0.0012 | 0.012 | 0.127 | 0.864 | 40.0 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00514 | 0.0012 | 0.009 | 0.047 | 0.252 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 0.00265 | 0.00072 | 0.009 | 0.072 | 0.512 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 0.00188 | 0.00049 | 0.010 | 0.094 | 0.709 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 0.00172 | 0.0006 | 0.010 | 0.133 | 0.868 | 40.0 |
| wilcoxon | 0.02 | 0.001 | 10 | 6.7e-04 | 6e-05 | 0.001 | 0.009 | 0.074 | 10.0 |
| wilcoxon | 0.02 | 0.001 | 20 | 2.6e-04 | 6e-05 | 0.001 | 0.016 | 0.220 | 20.0 |
| wilcoxon | 0.02 | 0.001 | 30 | 1.7e-04 | 6e-05 | 0.001 | 0.023 | 0.411 | 30.0 |
| wilcoxon | 0.02 | 0.001 | 40 | 1.6e-04 | 1e-05 | 0.001 | 0.030 | 0.625 | 40.0 |

## Rules under the dev4-gpu-kernels null (216 rounds; m = 3)

Current rule against the cap (minimum 5; with its confirmation, a second contest on later rounds):

| cap | false switch, m=1 | false switch, m=3 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 10% |
|---|---|---|---|---|---|---|---|
| 10 | <1e-12 | <1e-12 | 0.000 | 0.052 | 1.000 | 3.0 | 5.0 |
| 20 | <1e-12 | <1e-12 | 0.000 | 0.059 | 1.000 | 5.0 | 5.0 |
| 30 | <1e-12 | <1e-12 | 0.000 | 0.059 | 1.000 | 5.0 | 5.0 |
| 40 | <1e-12 | <1e-12 | 0.000 | 0.060 | 1.000 | 5.0 | 5.0 |

Exact sign test of "at least delta faster", group-sequential (one nominal level at every look from round 5, the largest within alpha, by DP for the cap); Holm over m arms (alpha / m per arm); power for one gaining arm at alpha / m:

| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=3 | power 2% | power 5% | power 10% | rounds at gain 0 | rounds at 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | 10 | 0.0078 | 0.00781 | 0.0077 | 0.0058 | 1.000 | 1.000 | 1.000 | 2.0 | 9.0 |
| 0 | 0.01 | 20 | 0.0092 | 0.00391 | 0.0099 | 0.011 | 1.000 | 1.000 | 1.000 | 8.0 | 10.0 |
| 0 | 0.01 | 30 | 0.0099 | 0.0036 | 0.011 | 0.011 | 1.000 | 1.000 | 1.000 | 16.0 | 10.0 |
| 0 | 0.01 | 40 | 0.0099 | 0.00299 | 0.011 | 0.011 | 1.000 | 1.000 | 1.000 | 22.0 | 11.0 |
| 0 | 0.001 | 10 | 0.00098 | 9.8e-04 | 0.0011 | no test at alpha/m | - | - | - | 2.0 | - |
| 0 | 0.001 | 20 | 0.00064 | 3.6e-04 | 0.0007 | 0.00069 | 1.000 | 1.000 | 1.000 | 6.0 | 13.0 |
| 0 | 0.001 | 30 | 0.00096 | 3.6e-04 | 0.0011 | 0.001 | 1.000 | 1.000 | 1.000 | 12.1 | 13.0 |
| 0 | 0.001 | 40 | 0.001 | 2.6e-04 | 0.0011 | 0.0011 | 1.000 | 1.000 | 1.000 | 18.1 | 14.0 |
| 0 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | 9.7e-05 | 0.0001 | 1.000 | 1.000 | 1.000 | 4.0 | 16.0 |
| 0 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | 0.0001 | 0.0001 | 1.000 | 1.000 | 1.000 | 10.1 | 17.0 |
| 0 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | 0.00011 | 0.00011 | 1.000 | 1.000 | 1.000 | 16.1 | 17.0 |
| 0.02 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.002 | 1.000 | 1.000 | 1.0 | 9.0 |
| 0.02 | 0.01 | 20 | 0.0092 | 0.00391 | <1e-12 | <1e-12 | 0.004 | 1.000 | 1.000 | 4.0 | 10.0 |
| 0.02 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.004 | 1.000 | 1.000 | 8.0 | 10.0 |
| 0.02 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.004 | 1.000 | 1.000 | 11.0 | 11.0 |
| 0.02 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | no test at alpha/m | - | - | - | 1.0 | - |
| 0.02 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 3.0 | 13.0 |
| 0.02 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 6.0 | 13.0 |
| 0.02 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 9.0 | 14.0 |
| 0.02 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.02 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 2.0 | 16.0 |
| 0.02 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 5.0 | 17.0 |
| 0.02 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 1.000 | 1.000 | 8.0 | 17.0 |
| 0.05 | 0.01 | 10 | 0.0078 | 0.00781 | <1e-12 | <1e-12 | 0.000 | 0.002 | 1.000 | 1.0 | 2.0 |
| 0.05 | 0.01 | 20 | 0.0092 | 0.00391 | <1e-12 | <1e-12 | 0.000 | 0.004 | 1.000 | 4.0 | 8.0 |
| 0.05 | 0.01 | 30 | 0.0099 | 0.0036 | <1e-12 | <1e-12 | 0.000 | 0.004 | 1.000 | 8.0 | 14.1 |
| 0.05 | 0.01 | 40 | 0.0099 | 0.00299 | <1e-12 | <1e-12 | 0.000 | 0.004 | 1.000 | 11.0 | 20.1 |
| 0.05 | 0.001 | 10 | 0.00098 | 9.8e-04 | <1e-12 | no test at alpha/m | - | - | - | 1.0 | - |
| 0.05 | 0.001 | 20 | 0.00064 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 3.0 | 4.0 |
| 0.05 | 0.001 | 30 | 0.00096 | 3.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 6.0 | 10.1 |
| 0.05 | 0.001 | 40 | 0.001 | 2.6e-04 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 9.0 | 18.1 |
| 0.05 | 0.0001 | 10 | no test within alpha in 10 rounds | | | | | | | | |
| 0.05 | 0.0001 | 20 | 8.8e-05 | 6.1e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 2.0 | 4.0 |
| 0.05 | 0.0001 | 30 | 9.3e-05 | 3.3e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 5.0 | 8.0 |
| 0.05 | 0.0001 | 40 | 9.3e-05 | 3.0e-05 | <1e-12 | <1e-12 | 0.000 | 0.000 | 1.000 | 8.0 | 14.1 |

Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from round 5, calibrated at alpha / m on 100000 simulated null contests):

| test | delta | alpha | cap | nominal level | false switch, m=3 | power 2% | power 5% | power 10% | rounds at gain 0 |
|---|---|---|---|---|---|---|---|---|---|
| t | 0 | 0.01 | 10 | 9.3e-04 | 0.011 | 1.000 | 1.000 | 1.000 | 10.0 |
| t | 0 | 0.01 | 20 | 4.8e-04 | 0.01 | 1.000 | 1.000 | 1.000 | 20.0 |
| t | 0 | 0.01 | 30 | 3.9e-04 | 0.0098 | 1.000 | 1.000 | 1.000 | 29.9 |
| t | 0 | 0.01 | 40 | 3.3e-04 | 0.012 | 1.000 | 1.000 | 1.000 | 39.9 |
| t | 0.02 | 0.01 | 10 | 8.9e-04 | <1e-12 | 0.003 | 1.000 | 1.000 | 10.0 |
| t | 0.02 | 0.01 | 20 | 5.3e-04 | <1e-12 | 0.003 | 1.000 | 1.000 | 20.0 |
| t | 0.02 | 0.01 | 30 | 3.7e-04 | <1e-12 | 0.003 | 1.000 | 1.000 | 30.0 |
| t | 0.02 | 0.01 | 40 | 3.0e-04 | <1e-12 | 0.004 | 1.000 | 1.000 | 40.0 |
| wilcoxon | 0 | 0.01 | 10 | 0.00212 | 0.0077 | 0.985 | 0.985 | 0.985 | 10.0 |
| wilcoxon | 0 | 0.01 | 20 | 9.3e-04 | 0.01 | 1.000 | 1.000 | 1.000 | 20.0 |
| wilcoxon | 0 | 0.01 | 30 | 6.4e-04 | 0.0087 | 1.000 | 1.000 | 1.000 | 30.0 |
| wilcoxon | 0 | 0.01 | 40 | 4.9e-04 | 0.009 | 1.000 | 1.000 | 1.000 | 39.9 |
| wilcoxon | 0.02 | 0.01 | 10 | 0.00207 | <1e-12 | 0.003 | 0.985 | 0.985 | 10.0 |
| wilcoxon | 0.02 | 0.01 | 20 | 9.5e-04 | <1e-12 | 0.003 | 1.000 | 1.000 | 20.0 |
| wilcoxon | 0.02 | 0.01 | 30 | 6.4e-04 | <1e-12 | 0.004 | 1.000 | 1.000 | 30.0 |
| wilcoxon | 0.02 | 0.01 | 40 | 5.2e-04 | <1e-12 | 0.004 | 1.000 | 1.000 | 40.0 |

