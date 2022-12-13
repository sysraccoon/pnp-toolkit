from dataclasses import dataclass, field
from typing import Dict

from PIL.Image import Image

from pnp_toolkit.core.binpack.output_types import PackedDocument


@dataclass
class RenderDocumentFlow:
    packed_document: PackedDocument
    front_images: Dict[int, Image]
    back_images: Dict[int, Image]

