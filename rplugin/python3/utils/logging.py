from logging import log as _log, basicConfig, DEBUG
from pathlib import Path
from typing import List, Optional
from inspect import stack

from pynvim.api import Nvim

from custom_types.log_level import LogLevel


class Logging:
    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        self.file_path = Path(__file__).resolve()
        self.plugin_path = Path(
            *self.file_path.parts[: self.file_path.parts.index("nvim-javagenie") + 1]
        )
        self.log_file_path = self.plugin_path.joinpath("logging.log")
        if not self.plugin_path.exists():
            raise FileNotFoundError
        basicConfig(
            filename=self.plugin_path.joinpath("logging.log"),
            level=DEBUG,
            format="[%(asctime)s - %(name)s - %(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.last_call_stack: Optional[str] = None

    @staticmethod
    def get_caller_params():
        call_stack = stack()
        caller_frame = call_stack[2].frame
        return caller_frame.f_locals

    def build_call_stack(self) -> str:
        call_stack: list[str] = []
        for i, s in enumerate(stack()):
            class_name = s[0].f_locals["self"].__class__.__name__
            method_name = s[0].f_code.co_name
            if class_name == "Host":
                break
            if i == 0:
                continue
            if class_name != "Logging" and method_name != "log":
                call_stack.append(method_name)
                call_stack.append(class_name)
        return ":".join(reversed(call_stack))

    def reset_log_file(self) -> None:
        if self.log_file_path.exists() and self.log_file_path.is_file():
            self.log_file_path.write_text("")
        self.last_call_stack = None

    def log(
        self,
        msg: str | List[str],
        level: LogLevel,
    ) -> None:
        level_int: int
        match level:
            case LogLevel.INFO:
                level_int = 20
            case LogLevel.CRITICAL:
                level_int = 50
            case LogLevel.ERROR:
                level_int = 40
            case LogLevel.WARN:
                level_int = 30
            case _:
                level_int = 10
        if isinstance(msg, list):
            msg = "\n".join(msg)
        log_msg = ""
        call_stack = self.build_call_stack()
        if call_stack != self.last_call_stack:
            log_msg += f"[{call_stack}]:\nParams:\n"
            params = self.get_caller_params()
            if params is not None:
                for k, v in params.items():
                    log_msg += f"{k}: {v}\n"
                log_msg += "\n"
        log_msg += msg
        _log(level_int, log_msg)
        self.last_call_stack = call_stack

    def echomsg(self, msg: str) -> None:
        self.nvim.command(f"echomsg '{msg}'")
