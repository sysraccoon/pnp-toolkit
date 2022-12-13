import abc
from dataclasses import dataclass


@dataclass
class Position:
    x: float
    y: float


@dataclass
class Size:
    width: float
    height: float

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class Padding:
    top: float
    right: float
    bottom: float
    left: float


@dataclass
class UnpackedItem:
    id: int
    size: Size
    back_exists: bool = False


class PaperSpec(metaclass=abc.ABCMeta):
    pass


@dataclass
class SimplePaperSpec(PaperSpec):
    size: Size
    padding: Padding


@dataclass
class RollPaperSpec(PaperSpec):
    width: float
    padding: Padding

