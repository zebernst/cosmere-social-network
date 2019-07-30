
class InteractionNetworkConfig:
    run_size = 25  # tokens
    prev_cxt_lines = 4
    next_cxt_lines = 3
    default_min_weight = 3


class FamilyNetworkConfig:
    default_min_component_size = 2
    relation_fields = ('parents', 'siblings', 'spouse', 'children', 'bonded')  # currently: nuclear family only
    _unused_fields = ('descendants', 'ancestors', 'family', 'relatives')
