from pynvim import plugin
from pynvim.api import Nvim

from base import Base


@plugin
class JavaFileCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)
