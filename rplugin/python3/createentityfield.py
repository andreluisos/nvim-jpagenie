from pathlib import Path
from typing import Literal

from pynvim.api.nvim import Nvim
from tree_sitter import Node

from tsutil import TreesitterUtil
from messaging import Messaging
from constants.java_types import JAVA_TYPES
from re import sub


class CreateEntityField:
    def __init__(
        self,
        nvim: Nvim,
        tsutil: TreesitterUtil,
        messaging: Messaging,
    ):
        self.nvim = nvim
        self.tsutil = tsutil
        self.messaging = messaging
        self.java_types = JAVA_TYPES
        self.all_field_declarations_query = "(field_declaration) @field"
        self.class_body_query = "(class_body) @body"

    def get_available_types(self) -> list[list[str | tuple[str, str | None]]]:
        return [[f"{t[0]} ({t[1]})", t] for t in self.java_types]

    def get_insert_point(self, buffer_path: Path, debugger: bool = False) -> int:
        buffer_node = self.tsutil.get_node_from_path(buffer_path, debugger)
        field_declarations = self.tsutil.query_node(
            buffer_node, self.all_field_declarations_query, debugger
        )
        field_declarations_count = len(field_declarations)
        if field_declarations_count != 0:
            # != 0 means there are existing field declarations
            last_field: Node = field_declarations[field_declarations_count - 1][0]
            position = (last_field.start_byte, last_field.end_byte)
            if debugger:
                self.messaging.log(
                    f"field_declarations_count: {field_declarations_count}", "debug"
                )
                self.messaging.log(f"position: {position}", "debug")
            return position[1]
        class_body = self.tsutil.query_node(
            buffer_node, self.class_body_query, debugger
        )
        if len(class_body) != 1:
            self.messaging.log(
                "Couldn't find the class declaration.", "error", send_msg=True
            )
            raise ValueError("Couldn't find the class declaration.")
        position = (
            class_body[0][0].start_byte,
            class_body[0][0].end_byte,
        )
        if debugger:
            self.messaging.log(f"class body count: {len(class_body)}", "debug")
            self.messaging.log(f"position: {position}", "debug")
        return position[0] + 1

    def generate_basic_field_template(
        self,
        field_type: str,
        field_name: str,
        nullable: bool = True,
        unique: bool = False,
        large_object: bool = False,
        debugger: bool = False,
    ) -> str:
        snaked_field_name = sub(r"(?<!^)(?=[A-Z])", "_", field_name).lower()
        extra_column_params = ""
        template = ""
        if nullable:
            extra_column_params += ", nullable = true"
        if unique:
            extra_column_params += ", unique = true"
        if large_object:
            template += "@Lob\n"
        column_body = f'@Column(name = "{snaked_field_name}"{extra_column_params})\n'
        field_body = f"private {field_type} {field_name};"
        template += column_body + field_body
        if debugger:
            self.messaging.log(
                f"field type: {field_type}, field name: {field_name}, "
                f"nullable: {nullable}, unique: {unique}, large object: {large_object}",
                "debug",
            )
            self.messaging.log(f"template:\n{template}", "debug")
        return template

    def generate_enum_field_template(
        self,
        field_type: str,
        field_name: str,
        enum_type: Literal["ORDINAL", "STRING"] = "ORDINAL",
        string_length: int = 2,
        nullable: bool = False,
        unique: bool = False,
        debugger: bool = False,
    ) -> str:
        if enum_type == "STRING" and string_length == 0:
            error_message = "When enum_type is STRING, a valid length must be defined."
            self.messaging.log(error_message, "error")
            raise ValueError(error_message)
        template = ""
        enum_body = f"@Enumerated(EnumType.{enum_type})\n"
        field_template = self.generate_basic_field_template(
            field_type, field_name, nullable, unique, debugger=debugger
        )
        template += enum_body + field_template
        if debugger:
            self.messaging.log(
                f"field type: {field_type}, field name: {field_name}, enum type: {enum_type},"
                f"string length: {string_length}, nullable: {nullable}, unique: {unique}",
                "debug",
            )
            self.messaging.log(f"template:\n{template}", "debug")
        return template

    def create_basic_entity_field(
        self,
        buffer_path: Path,
        field_type: str,
        field_name: str,
        nullable: bool = True,
        unique: bool = False,
        large_object: bool = False,
        debugger: bool = False,
    ) -> None:
        template = "\n\n" + self.generate_basic_field_template(
            field_type, field_name, nullable, unique, large_object, debugger
        )
        insert_position = self.get_insert_point(buffer_path, debugger)
        self.tsutil.insert_code_into_position(
            template, insert_position, buffer_path, debugger
        )
        type_import_path = (
            f"import {self.tsutil.get_field_type_import_path(field_type, debugger)};"
        )
        if type_import_path is not None:
            self.tsutil.insert_import_path_into_buffer(
                buffer_path, type_import_path, debugger
            )
        if debugger:
            self.messaging.log(
                f"buffer path: {buffer_path}"
                f"field type: {field_type}, field name: {field_name}, "
                f"nullable: {nullable}, unique: {unique}, large object: {large_object}",
                "debug",
            )
        self.messaging.log(f"insert position: {insert_position}", "debug")
        self.messaging.log(f"type import path: {type_import_path}", "debug")
        self.messaging.log(f"template:\n{template}", "debug")
        self.tsutil.reload_format_organize_buffer(buffer_path)

    def create_enum_entity_field(
        self,
        buffer_path: Path,
        field_type: str,
        field_name: str,
        enum_type: Literal["ORDINAL", "STRING"] = "ORDINAL",
        string_length: int = 2,
        nullable: bool = False,
        unique: bool = False,
        debugger: bool = False,
    ) -> None:
        template = "\n\n" + self.generate_enum_field_template(
            field_type, field_name, enum_type, string_length, nullable, unique, debugger
        )
        insert_position = self.get_insert_point(buffer_path, debugger)
        self.tsutil.insert_code_into_position(
            template, insert_position, buffer_path, debugger
        )
        type_import_path = (
            f"import {self.tsutil.get_field_type_import_path(field_type, debugger)};"
        )
        enumerated_import_path = "import jakarta.persistence.Enumerated;"
        if type_import_path is not None:
            self.tsutil.insert_import_path_into_buffer(
                buffer_path, type_import_path, debugger
            )
        self.tsutil.insert_import_path_into_buffer(
            buffer_path, enumerated_import_path, debugger
        )
        if debugger:
            self.messaging.log(
                f"buffer path: {buffer_path}"
                f"field type: {field_type}, field name: {field_name}, "
                f"nullable: {nullable}, unique: {unique}",
                "debug",
            )
        self.messaging.log(f"insert position: {insert_position}", "debug")
        self.messaging.log(f"type import path: {type_import_path}", "debug")
        self.messaging.log(f"enumerated import path: {enumerated_import_path}", "debug")
        self.messaging.log(f"template:\n{template}", "debug")
        self.tsutil.reload_format_organize_buffer(buffer_path)
