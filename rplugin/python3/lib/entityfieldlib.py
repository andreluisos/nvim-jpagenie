from pathlib import Path
from re import sub
from typing import Literal

from pynvim.api.nvim import Nvim
from tree_sitter import Node

from lib.treesitterlib import TreesitterLib
from util.logging import Logging


class EntityFieldLib:
    def __init__(
        self,
        nvim: Nvim,
        java_basic_types: list[tuple],
        treesitter_lib: TreesitterLib,
        logging: Logging,
    ):
        self.nvim = nvim
        self.treesitter_lib = treesitter_lib
        self.logging = logging
        self.java_basic_types = java_basic_types
        self.all_field_declarations_query = "(field_declaration) @field"
        self.class_body_query = "(class_body) @body"

    def get_available_types(self) -> list[list[str | tuple[str, str | None]]]:
        return [[f"{t[0]} ({t[1]})", t] for t in self.java_basic_types]

    def get_field_insert_point(self, buffer_bytes: bytes, debug: bool = False) -> int:
        buffer_node = self.treesitter_lib.get_node_from_bytes(buffer_bytes)
        field_declarations = self.treesitter_lib.query_node(
            buffer_node, self.all_field_declarations_query, debug
        )
        field_declarations_count = len(field_declarations)
        if field_declarations_count != 0:
            # != 0 means there are existing field declarations
            last_field: Node = field_declarations[field_declarations_count - 1][0]
            position = (last_field.start_byte, last_field.end_byte)
            if debug:
                self.logging.log(
                    f"field_declarations_count: {field_declarations_count}", "debug"
                )
                self.logging.log(f"position: {position}", "debug")
            return position[1]
        class_body = self.treesitter_lib.query_node(
            buffer_node, self.class_body_query, debug
        )
        if len(class_body) != 1:
            self.logging.log(
                "Couldn't find the class declaration.",
                "error",
            )
            raise ValueError("Couldn't find the class declaration.")
        position = (
            class_body[0][0].start_byte,
            class_body[0][0].end_byte,
        )
        if debug:
            self.logging.log(f"class body count: {len(class_body)}", "debug")
            self.logging.log(f"position: {position}", "debug")
        return position[0] + 1

    def generate_basic_field_template(
        self,
        field_type: str,
        field_name: str,
        nullable: bool = True,
        unique: bool = False,
        large_object: bool = False,
        debug: bool = False,
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
        if debug:
            self.logging.log(
                f"field type: {field_type}, field name: {field_name}, "
                f"nullable: {nullable}, unique: {unique}, large object: {large_object}",
                "debug",
            )
            self.logging.log(f"template:\n{template}", "debug")
        return template

    def generate_enum_field_template(
        self,
        field_type: str,
        field_name: str,
        enum_type: Literal["ORDINAL", "STRING"] = "ORDINAL",
        string_length: int = 2,
        nullable: bool = False,
        unique: bool = False,
        debug: bool = False,
    ) -> str:
        if enum_type == "STRING" and string_length == 0:
            error_message = "When enum_type is STRING, a valid length must be defined."
            self.logging.log(error_message, "error")
            raise ValueError(error_message)
        template = ""
        enum_body = f"@Enumerated(EnumType.{enum_type})\n"
        field_template = self.generate_basic_field_template(
            field_type, field_name, nullable, unique, debug=debug
        )
        template += enum_body + field_template
        if debug:
            self.logging.log(
                [
                    f"field type: {field_type}, field name: {field_name}, enum type: {enum_type},"
                    f"string length: {string_length}, nullable: {nullable}, unique: {unique}"
                ],
                "debug",
            )
            self.logging.log(f"template:\n{template}", "debug")
        return template

    def create_basic_entity_field(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_type: str,
        field_name: str,
        nullable: bool = True,
        unique: bool = False,
        large_object: bool = False,
        debug: bool = False,
    ) -> None:
        template = "\n\n" + self.generate_basic_field_template(
            field_type, field_name, nullable, unique, large_object, debug
        )
        new_source = self.treesitter_lib.insert_import_path_into_buffer(
            buffer_bytes, "jakarta.persistence.Column", debug
        )
        type_import_path = self.treesitter_lib.get_field_type_import_path(
            field_type, debug
        )
        if type_import_path:
            new_source = self.treesitter_lib.insert_import_path_into_buffer(
                new_source, type_import_path, debug
            )
        insert_position = self.get_field_insert_point(new_source, debug)
        class_body_position = self.treesitter_lib.query_node(
            self.treesitter_lib.get_node_from_bytes(new_source),
            self.class_body_query,
            debug,
        )[0][0].start_byte
        if insert_position < class_body_position:
            insert_position = class_body_position + 1
        new_source = self.treesitter_lib.insert_code_into_position(
            template, insert_position, new_source, debug
        )
        if debug:
            self.logging.log(
                [
                    f"buffer path: {buffer_path}\n"
                    f"field type: {field_type}\n"
                    f"field name: {field_name}\n"
                    f"nullable: {nullable}\n"
                    f"unique: {unique}\n"
                    f"insert position: {insert_position}\n"
                    f"type import path: {type_import_path}\n"
                    f"template:\n{template}\n"
                    f"buffer before:\n{buffer_bytes.decode('utf-8')}\n"
                    f"buffer after:\n{buffer_bytes.decode('utf-8')}\n"
                ],
                "debug",
            )
        self.treesitter_lib.save_buffer(
            new_source, buffer_path, format=True, organize_imports=True
        )

    def create_enum_entity_field(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_type: str,
        field_name: str,
        enum_type: Literal["ORDINAL", "STRING"] = "ORDINAL",
        string_length: int = 2,
        nullable: bool = False,
        unique: bool = False,
        debug: bool = False,
    ) -> None:
        new_source: bytes
        buffer_bytes = self.treesitter_lib.get_bytes_from_path(buffer_path, debug)
        template = "\n\n" + self.generate_enum_field_template(
            field_type, field_name, enum_type, string_length, nullable, unique, debug
        )
        insert_position = self.get_field_insert_point(buffer_bytes, debug)
        new_source = self.treesitter_lib.insert_code_into_position(
            template, insert_position, buffer_bytes, debug
        )
        type_import_path = self.treesitter_lib.get_field_type_import_path(
            field_type, debug
        )
        enumerated_import_path = "jakarta.persistence.Enumerated"
        enumtype_import_path = "jakarta.persistence.EnumType"
        if type_import_path is not None:
            new_source = self.treesitter_lib.insert_import_path_into_buffer(
                new_source, type_import_path, debug
            )
        new_source = self.treesitter_lib.insert_import_path_into_buffer(
            new_source, enumerated_import_path, debug
        )
        new_source = self.treesitter_lib.insert_import_path_into_buffer(
            new_source, enumtype_import_path, debug
        )
        if debug:
            self.logging.log(
                [
                    f"buffer path: {buffer_path}\n"
                    f"field type: {field_type}\n"
                    f"field name: {field_name}\n"
                    f"enum type: {enum_type}\n"
                    f"lenght: {string_length}\n"
                    f"nullable: {nullable}\n"
                    f"unique: {unique}\n"
                    f"insert position: {insert_position}\n"
                    f"type import path: {type_import_path}\n"
                    f"enumerated import path: {enumerated_import_path}\n"
                    f"template:\n{template}\n"
                    f"buffer before:\n{buffer_bytes.decode('utf-8')}\n"
                    f"buffer after:\n{buffer_bytes.decode('utf-8')}\n"
                ],
                "debug",
            )
        self.treesitter_lib.save_buffer(new_source, buffer_path, True, True)
