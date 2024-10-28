from pathlib import Path


class FileUtils:
    def __init__(self) -> None:
        pass

    @staticmethod
    def read_ui_file_as_string(file_name: str) -> str:
        file_path = (
            Path(__file__).parent.resolve().parent.joinpath("ui").joinpath(file_name)
        )
        with open(file_path, "r") as f:
            return f.read().strip()
