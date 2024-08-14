from logging import log as _log, basicConfig, DEBUG
from typing import List, Literal
from inspect import stack


class Logging:
    def __init__(self, nvim):
        basicConfig(
            filename="logging.log",
            level=DEBUG,
            format="[%(asctime)s - %(name)s - %(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.nvim = nvim

    def build_call_stack(self) -> str:
        call_stack: list[str] = []
        for i, s in enumerate(stack()):
            class_name = s[0].f_locals["self"].__class__.__name__
            method_name = s[0].f_code.co_name
            if class_name == "Host":
                break
            if i == 0:
                continue
            call_stack.append(method_name)
            call_stack.append(class_name)
        return ":".join(reversed(call_stack))

    def log(
        self,
        msg: str | List[str],
        level: Literal["debug", "info", "critical", "error", "warn"],
    ) -> None:
        call_stack = self.build_call_stack()
        level_int: int
        match level:
            case "info":
                level_int = 20
            case "critical":
                level_int = 50
            case "error":
                level_int = 40
            case "warn":
                level_int = 30
            case _:
                level_int = 10
        if isinstance(msg, list):
            msg = "\n".join(msg)
        _log(level_int, f"[{call_stack}]:\n{msg}")
