"""The gate chain's model choices: the tables that hold a hierarchical plan's priced chains
(HierarchicalFilter._choose_chain) and the shortlist a joint trial's chain arms come from
(_trial; time_domain.TimeDomainFilterBank._joint_arms, HierarchicalFilter._trial_arms)."""


#: (chain-choice key, chain) -> whether the cost model prices the Q15 screen cheaper
_Q15_MODEL = {}


#: (n, snr, fd, tiers, window, profile signature, device, gate kind, direct) -> (model's
#: chain, shortlist, every chain the gate model covers)
_CHAIN_CHOICE = {}


#: Relative cost margin inside which other chains are proposed as trial arms: the model's
#: demonstrated error (tier costs agreed with the engine counters to ~25% in the consumer).
_CHAIN_MARGIN = 0.30


_CHAIN_SHORTLIST_MAX = 4


#: On a GPU the model's best three chains are proposed whatever their modelled gap: it prices
#: device work only, and missed the faster chain by 38% (HierarchicalFilter._choose_chain).
_CHAIN_SHORTLIST_GPU = 3
