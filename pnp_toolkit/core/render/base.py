import abc

from pnp_toolkit.core.render.types import RenderDocumentFlow


class OutputRenderer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def render(self, render_flow: RenderDocumentFlow):
        pass
