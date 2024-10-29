from pathlib import Path

from utils.logging import Logging


class FileUtils:
    def __init__(self, logging: Logging) -> None:
        self.logging = logging

    def read_ui_file_as_string(self, file_name: str, debug: bool = False) -> str:
        file_path = (
            Path(__file__).parent.resolve().parent.joinpath("ui").joinpath(file_name)
        )
        with open(file_path, "r") as f:
            file_content_str = f.read().strip()
            if debug:
                self.logging.log(
                    [
                        f"File path: {str(file_path)}",
                        f"File content:\n{file_content_str}",
                    ],
                    "debug",
                )
            return file_content_str
