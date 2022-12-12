from enum import Enum


class QcStrategy(Enum):
    """
    Represents a quality control strategy.
    todo: unify qc strategy enums
    """

    # Conventional FIFO assembly
    conventional_assembly = 1
    # Selective assembly with classes
    selective_assembly = 2
    # Individual assembly (first fit)
    individual_assembly = 3
    # Individual assembly (best fit)
    individual_assembly_greedy = 4
    # Solve individual assembly using Simplex
    individual_assembly_simplex = 5
    # Sorts main components ascending and mating components descending
    ascending_descending = 6
    # Sorts a group of main components ascending and mating components descending
    ascending_descending_grouped = 7
