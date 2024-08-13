from typing import Any, List, Callable
from constants.java_types import JAVA_TYPES
from messaging import Messaging


class ArgValidator:
    def __init__(self, messaging: Messaging) -> None:
        self.messaging = messaging
        self.java_types = JAVA_TYPES
        self.invalid_arg_type_msg = "Invalid argument type."

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
        if value in [k[0] for k in self.java_types]:
            return value
        raise ValueError(f"{value} is not a valid Java basic type.")

    def is_valid_java_file_name(self, value: str) -> str:
        if value in ["class", "interface", "record", "enum", "annotation"]:
            return value
        raise ValueError(f"{value} is not a valid Java file type")

    def validate_args_length(self, args: Any, required_len: int) -> None:
        if len(args) != required_len:
            error_msg = f"{required_len} arguments are required."
            self.messaging.log(error_msg, "error")
            raise ValueError(error_msg)

    def validate_args_type(
        self, args: List[str], required_types: List[str]
    ) -> List[Any]:
        if len(args) != len(required_types):
            error_msg = (
                "The number of arguments and the number of required types must match."
            )
            self.messaging.log(error_msg, "error")
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
                    self.messaging.log(self.invalid_arg_type_msg, "error")
                    raise ValueError(f"Cannot convert {arg} to {required_type}")
            else:
                self.messaging.log(self.invalid_arg_type_msg, "error")
                raise ValueError(f"Unsupported type: {required_type}")

        return converted_args
