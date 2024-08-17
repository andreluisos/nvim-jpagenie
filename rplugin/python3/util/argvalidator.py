from typing import Any, Callable, List

from util.logging import Logging


class ArgValidator:
    def __init__(self, java_basic_types: list[tuple], logging: Logging) -> None:
        self.logging = logging
        self.java_basic_types = java_basic_types
        self.invalid_arg_type_msg = "Invalid argument type."

    def clean_up_args(self, args: List[str]) -> List[str]:
        if "debug" in args:
            args.remove("debug")
        return args

    def attach_debugger(self, args: List[str]) -> bool:
        if "debug" in args:
            return True
        return False

    def is_boolean(self, value: str) -> bool:
        valid_true = {"true", "1", "yes", "on"}
        valid_false = {"false", "0", "no", "off"}
        return value.lower() in valid_true or value.lower() in valid_false

    def convert_to_bool(self, value: str) -> bool:
        if value.lower() in {"true", "1", "yes", "on"}:
            return True
        elif value.lower() in {"false", "0", "no", "off"}:
            return False
        else:
            raise ValueError(self.invalid_arg_type_msg)

    def convert_to_int(self, value: str) -> int:
        try:
            return int(value)
        except ValueError:
            raise ValueError(self.invalid_arg_type_msg)

    def convert_to_float(self, value: str) -> float:
        try:
            return float(value)
        except ValueError:
            raise ValueError(self.invalid_arg_type_msg)

    def convert_to_enum(self, value: str) -> str:
        if value in {"ORDINAL", "STRING"}:
            return value
        raise ValueError(self.invalid_arg_type_msg)

    def convert_to_java_type(self, value: str) -> str:
        if value in [k[0] for k in self.java_basic_types]:
            return value
        raise ValueError(f"{value} is not a valid Java basic type.")

    def is_valid_java_file_name(self, value: str) -> str:
        if value in ["class", "interface", "record", "enum", "annotation"]:
            return value
        raise ValueError(f"{value} is not a valid Java file type")

    def validate_args_length(self, args: List[str], required_len: int) -> None:
        clean_args = args
        if self.attach_debugger(args):
            clean_args = self.clean_up_args(args)
        if len(clean_args) != required_len:
            error_msg = f"{required_len} arguments are required."
            self.logging.log(error_msg, "error")
            raise ValueError(error_msg)

    def validate_args_type(
        self, args: List[str], required_types: List[str]
    ) -> List[Any]:
        if len(args) != len(required_types):
            error_msg = (
                "The number of arguments and the number of required types must match."
            )
            self.logging.log(error_msg, "error")
            raise ValueError(error_msg)

        type_conversion_map: dict[str, Callable[[str], Any]] = {
            "bool": self.convert_to_bool,
            "int": self.convert_to_int,
            "float": self.convert_to_float,
            "str": str,
            "enum": self.convert_to_enum,
            "java_type": self.convert_to_java_type,
            "java_file": self.is_valid_java_file_name,
        }

        converted_args = []
        for arg, required_type in zip(args, required_types):
            if required_type in type_conversion_map:
                try:
                    converted_args.append(type_conversion_map[required_type](arg))
                except ValueError:
                    self.logging.log(self.invalid_arg_type_msg, "error")
                    raise ValueError(f"Cannot convert {arg} to {required_type}")
            else:
                self.logging.log(self.invalid_arg_type_msg, "error")
                raise ValueError(f"Unsupported type: {required_type}")

        return converted_args
