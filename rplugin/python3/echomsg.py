class EchoMsg:
    def __init__(self, nvim):
        self.nvim = nvim

    def print(self, msg: str) -> None:
        self.nvim.command(f"echomsg '{msg}'")
