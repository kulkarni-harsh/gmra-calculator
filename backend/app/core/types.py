from typing import TypedDict


class SexAgeCounts(TypedDict):
    M: dict[str, int]
    F: dict[str, int]
    Total: int


ZipPopulationMap = dict[str, SexAgeCounts]
