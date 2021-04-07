"""
Plotting public API

Refer to pandas package
(https://github.com/pandas-dev/pandas/tree/master/pandas/plotting) for
example of file organization.
"""

from ._nats_functions import (
    get_gate_lat_lon_from_nats
)

from ._iff_functions import (
    get_departure_airport_from_iff,
    get_arrival_airport_from_iff,
    get_departure_gate_and_rwy_from_iff,
    get_arrival_gate_and_rwy_from_iff,
    random_airport_gate_and_rwy,
    check_if_flight_has_departed,
    check_if_flight_landing_in_dataset
)
