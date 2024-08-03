import logging
from typing import Literal
from inspect import stack


class Messaging:
    def __init__(self, nvim):
        self.logging = logging
        self.logging.basicConfig(
            filename="logging.log",
            level=logging.DEBUG,
            format="[%(asctime)s - %(name)s - %(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.nvim = nvim

    def print(self, msg: str):
        escaped_msg = msg.replace("'", "''")
        self.nvim.command(f"echomsg '{escaped_msg}'")

    def log(
        self,
        msg: str,
        level: Literal["debug", "info", "critical", "error", "warn"],
        send_msg: bool = False,
    ) -> None:
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
        self.logging.log(level_int, f"[{':'.join(reversed(call_stack))}]:\n{msg}")
        if send_msg:
            self.print(msg)
