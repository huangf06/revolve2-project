import math
from abc import abstractmethod

import multineat
import numpy as np
import numpy.typing as npt

from ...body.base import ActiveHinge, Body
from .._brain import Brain
from .._brain_instance import BrainInstance
from ._brain_cpg_instance import BrainCpgInstance
from ._make_cpg_network_structure_neighbor import (
    active_hinges_to_cpg_network_structure_neighbor,
)


class BrainCpgNetworkNeighbor(Brain):
    """
    A CPG brain with active hinges that are connected if they are within 2 jumps in the modular robot tree structure.

    That means, NOT grid coordinates, but tree distance.
    """

    _initial_state: npt.NDArray[np.float_]
    _weight_matrix: npt.NDArray[np.float_]  # nxn matrix matching number of neurons
    _output_mapping: list[tuple[int, ActiveHinge]]

    def __init__(self, body: Body, genotype: multineat.Genome) -> None:
        """
        Initialize this object.

        :param body: The body to create the cpg network and brain for.
        """
        self._active_hinges = body.find_modules_of_type(ActiveHinge)
        self.cpg_network_structure, self._output_mapping = active_hinges_to_cpg_network_structure_neighbor(
            self._active_hinges)
        self._connections = [
            (self._active_hinges[pair.cpg_index_lowest.index], self._active_hinges[pair.cpg_index_highest.index])
            for pair in self.cpg_network_structure.connections
        ]
        self._body = body
        self._genotype = genotype
        internal_weights, external_weights = self._make_weights(self._active_hinges, self._connections, self._body)
        self._weight_matrix = self.cpg_network_structure.make_connection_weights_matrix(
            {cpg: weight for cpg, weight in zip(self.cpg_network_structure.cpgs, internal_weights)},
            {pair: weight for pair, weight in zip(self.cpg_network_structure.connections, external_weights)}
        )
        self._initial_state = self.cpg_network_structure.make_uniform_state(0.5 * math.sqrt(2))

        self._update_timer = 0.0
        self._update_interval = 10.0


    def make_instance(self) -> BrainInstance:
        """
        Create an instance of this brain.

        :returns: The created instance.
        """
        return BrainCpgInstance(
            initial_state=self._initial_state,
            weight_matrix=self._weight_matrix,
            output_mapping=self._output_mapping,
            body=self._body,
            genotype=self._genotype
        )

    @abstractmethod
    def _make_weights(
        self,
        active_hinges: list[ActiveHinge],
        connections: list[tuple[ActiveHinge, ActiveHinge]],
        body: Body,
    ) -> tuple[list[float], list[float]]:
        """
        Define the weights between neurons.

        :param active_hinges: The active hinges corresponding to each cpg.
        :param connections: Pairs of active hinges corresponding to pairs of cpgs that are connected.
                            Connection is from hinge 0 to hinge 1.
                            Opposite connection is not provided as weights are assumed to be negative.
        :param body: The body that matches this brain.
        :returns: Two lists. The first list contains the internal weights in cpgs, corresponding to `active_hinges`
                 The second list contains the weights between connected cpgs, corresponding to `connections`
                 The lists should match the order of the input parameters.
        """
