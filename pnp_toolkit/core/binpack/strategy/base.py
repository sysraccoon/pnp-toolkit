import abc
from typing import List, Type

from pnp_toolkit.core.binpack.input_types import PaperSpec, UnpackedItem
from pnp_toolkit.core.binpack.output_types import PackedDocument


class PackStrategy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def pack(self, paper_spec: PaperSpec, components: List[UnpackedItem]) -> PackedDocument:
        pass

    @abc.abstractmethod
    def supported_paper(self) -> List[Type[PaperSpec]]:
        pass
