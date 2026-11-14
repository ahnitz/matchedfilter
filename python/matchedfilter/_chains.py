"""The gate chain's model choices: the tables that hold a hierarchical plan's priced chains and
the model's Q15 screen setting for each (HierarchicalFilter._choose_chain)."""


#: (chain-choice key, chain) -> whether the cost model prices the Q15 screen cheaper
_Q15_MODEL = {}


#: (n, snr, fd, tiers, window, profile signature, device, gate kind, direct) -> (model's
#: chain, every chain the gate model covers, in modelled cost order)
_CHAIN_CHOICE = {}


#: (n, snr, fd, tiers, window, device, candidate bands, the cheapest chain's first band
#: without shared screeners, reference profile signature) -> the first band whose shared
#: screeners won in the last plan for that reference: the band the next one clusters first
_TIER0_FIRST = {}
