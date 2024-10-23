from enum import Enum
from pathlib import Path
from re import sub
from typing import List, Literal, Optional

from pynvim.api.nvim import Nvim

from lib.treesitterlib import TreesitterLib
from lib.commonhelper import CommonHelper
from util.logging import Logging
from util.data_types import FieldTimeZoneStorage, FieldTemporal, EnumType


class EntityFieldLib:
    def __init__(
        self,
        nvim: Nvim,
        java_basic_types: list[tuple],
        treesitter_lib: TreesitterLib,
        common_helper: CommonHelper,
        logging: Logging,
    ):
        self.nvim = nvim
        self.treesitter_lib = treesitter_lib
        self.logging = logging
        self.java_basic_types = java_basic_types
        self.common_helper = common_helper
        self.importings: List[str] = []
        self.class_body_query = "(class_body) @body"

    def get_available_types(self) -> list[list[str | tuple[str, str | None]]]:
        return [[f"{t[0]} ({t[1]})", t] for t in self.java_basic_types]

    def generate_basic_field_template(
        self,
        field_package_path: str,
        field_name: str,
        field_length: Optional[int],
        field_precision: Optional[int],
        field_scale: Optional[int],
        field_time_zone_storage: Optional[FieldTimeZoneStorage],
        field_temporal: Optional[FieldTemporal],
        mandatory: bool = False,
        unique: bool = False,
        large_object: bool = False,
        debug: bool = False,
    ) -> str:
        field_type = (
            field_package_path.split(".")[-1]
            if "." in field_package_path
            else field_package_path
        )
        snaked_field_name = sub(r"(?<!^)(?=[A-Z])", "_", field_name).lower()
        column_params: List[str] = [f'name = "{snaked_field_name}"']
        template = ""
        self.importings.append("jakarta.persistence.Column")
        if "." in field_package_path:
            self.importings.append(field_package_path)
        if (
            field_package_path
            in [
                "java.lang.String",
                "java.net.URL",
                "java.util.Locale",
                "java.util.Currency",
                "java.lang.Class",
                "java.lang.Character[]",
                "char[]",
                "java.util.TimeZone",
                "java.time.ZoneOffset",
            ]
            and field_length != 255
        ):
            column_params.append(f"length = {field_length}")
        if (
            field_package_path
            in [
                "java.time.OffsetDateTime",
                "java.time.OffsetTime",
                "java.time.ZonedDateTime",
            ]
            and field_time_zone_storage is not None
        ):
            self.importings.extend(
                [
                    "org.hibernate.annotations.TimeZoneStorage",
                    "org.hibernate.annotations.TimeZoneStorageType",
                ]
            )
            template += (
                f"@TimeZoneStorage(TimeZoneStorageType.{field_time_zone_storage})\n"
            )
        if (
            field_package_path
            in [
                "java.util.Date",
                "java.util.Calendar",
            ]
            and field_temporal is not None
        ):
            self.importings.extend(
                ["jakarta.persistence.Temporal", "jakarta.persistence.TemporalType"]
            )
            template += f"@Temporal(TemporalType.{field_temporal})\n"
        if (
            field_package_path == "java.math.BigDecimal"
            and field_precision is not None
            and field_scale is not None
        ):
            column_params.extend(
                [f"precision = {field_precision}", f"scale = {field_scale}"]
            )
        if large_object:
            self.importings.append("jakarta.persistence.Lob")
            template += "@Lob\n"
        if mandatory:
            column_params.append("nullable = true")
        if unique:
            column_params.append("unique = true")
        column_body = f'@Column({", ".join(column_params)})\n'
        field_body = f"private {field_type} {field_name};"
        template += column_body + field_body
        if debug:
            self.logging.log(
                f"field type: {field_type}, field name: {field_name}, "
                f"mandatory: {mandatory}, unique: {unique}, large object: {large_object}",
                "debug",
            )
            self.logging.log(f"template:\n{template}", "debug")
        return template

    def generate_id_field_template(
        self,
        field_type: str,
        field_name: str,
        id_generation: Literal["none", "auto", "identity", "sequence"],
        nullable: bool = False,
        debug: bool = False,
    ) -> str:
        template = ""
        id_body = "@Id\n"
        generation_body = ""
        field_template = self.generate_basic_field_template(
            field_type, field_name, nullable, debug=debug
        )
        if id_generation in ["auto", "identity", "sequence"]:
            generation_body = (
                f"@GeneratedValue(strategy = GenerationType.{id_generation.upper()})\n"
            )
        template += id_body + generation_body + field_template
        if debug:
            self.logging.log(
                [
                    f"field type: {field_type}, field name: {field_name}, "
                    f"id generation: {id_generation}, nullable: {nullable}"
                    f"template:\n{template}"
                ],
                "debug",
            )
        return template

    def generate_enum_field_template(
        self,
        field_package_path: str,
        field_name: str,
        field_length: Optional[int],
        enum_type: Literal["ORDINAL", "STRING"] = "ORDINAL",
        mandatory: bool = False,
        unique: bool = False,
        debug: bool = False,
    ) -> str:
        template = ""
        enum_body = f"@Enumerated(EnumType.{enum_type})\n"
        field_name = self.common_helper.generate_field_name(
            field_type=field_type, plural=False, debug=debug
        )
        field_template = self.generate_basic_field_template(
            field_package_path,
            field_name,
            field_length,
            None,
            None,
            None,
            None,
            mandatory,
            unique,
            debug=debug,
        )
        template += enum_body + field_template
        # if debug:
        #     self.logging.log(
        #         [
        #             f"field type: {field_type}, field name: {field_name}, enum type: {enum_type},"
        #             f"string length: {string_length}, nullable: {nullable}, unique: {unique}"
        #             f"template:\n{template}"
        #         ],
        #         "debug",
        #     )
        return template

    def create_basic_entity_field(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_package_path: str,
        field_name: str,
        field_length: int,
        field_precision: int,
        field_scale: int,
        field_time_zone_storage: Optional[FieldTimeZoneStorage],
        field_temporal: Optional[FieldTemporal],
        mandatory: bool,
        unique: bool,
        large_object: bool,
        debug: bool = False,
    ) -> None:
        template = "\n\n" + self.generate_basic_field_template(
            field_package_path=field_package_path,
            field_name=field_name,
            field_length=field_length,
            field_precision=field_precision,
            field_scale=field_scale,
            field_time_zone_storage=field_time_zone_storage,
            field_temporal=field_temporal,
            mandatory=mandatory,
            unique=unique,
            large_object=large_object,
            debug=debug,
        )
        buffer_bytes = self.common_helper.add_imports_to_buffer(
            self.importings, buffer_bytes, debug
        )
        insert_position = self.treesitter_lib.get_entity_field_insert_point(
            buffer_bytes, debug
        )
        class_body_position = self.treesitter_lib.query_node(
            self.treesitter_lib.get_node_from_bytes(buffer_bytes),
            self.class_body_query,
            debug,
        )[0][0].start_byte
        if insert_position < class_body_position:
            insert_position = class_body_position + 1
        new_source = self.treesitter_lib.insert_code_into_position(
            template, insert_position, buffer_bytes, debug
        )
        if debug:
            self.logging.log(
                [
                    f"buffer path: {buffer_path}\n"
                    f"field name: {field_name}\n"
                    f"unique: {unique}\n"
                    f"insert position: {insert_position}\n"
                    f"template:\n{template}\n"
                    f"buffer before:\n{buffer_bytes.decode('utf-8')}\n"
                    f"buffer after:\n{buffer_bytes.decode('utf-8')}\n"
                ],
                "debug",
            )
        self.treesitter_lib.update_buffer(new_source, buffer_path, False, True, True)

    def create_enum_entity_field(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_package_path: str,
        field_name: str,
        field_length: Optional[int],
        enum_type: EnumType = "ORDINAL",
        mandatory: bool = False,
        unique: bool = False,
        debug: bool = False,
    ) -> None:
        new_source: bytes
        field_type = field_package_path.split(".")[-1]
        template = "\n\n" + self.generate_enum_field_template(
            field_package_path,
            field_name,
            field_length,
            enum_type,
            mandatory,
            unique,
            debug,
        )
        importings: List[str] = [
            "jakarta.persistence.Enumerated",
            "jakarta.persistence.EnumType",
        ]
        insert_position = self.treesitter_lib.get_entity_field_insert_point(
            buffer_bytes, debug
        )
        new_source = self.treesitter_lib.insert_code_into_position(
            template, insert_position, buffer_bytes, debug
        )
        type_import_path = self.treesitter_lib.get_field_type_import_path(
            field_type, debug
        )
        if type_import_path is not None:
            importings.append(type_import_path)
        new_source = self.treesitter_lib.insert_import_paths_into_buffer(
            new_source, importings, debug
        )
        if debug:
            self.logging.log(
                [
                    f"buffer path: {buffer_path}\n"
                    f"field type: {field_type}\n"
                    f"field name: {field_name}\n"
                    f"enum type: {enum_type}\n"
                    f"lenght: {field_length}\n"
                    f"mandatory: {mandatory}\n"
                    f"unique: {unique}\n"
                    f"insert position: {insert_position}\n"
                    f"type import path: {importings[2] if len(importings) >=2 else None}\n"
                    f"enumerated import path: {importings[0]}\n"
                    f"enumtype import path: {importings[1]}\n"
                    f"template:\n{template}\n"
                    f"buffer before:\n{buffer_bytes.decode('utf-8')}\n"
                    f"buffer after:\n{buffer_bytes.decode('utf-8')}\n"
                ],
                "debug",
            )
            self.treesitter_lib.update_buffer(
                new_source, buffer_path, False, True, True
            )

    def create_id_entity_field(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_type: str,
        field_name: str,
        id_generation: Literal["none", "auto", "identity", "sequence"],
        nullable: bool = False,
        debug: bool = False,
    ) -> None:
        new_source: bytes
        importings: List[str] = [
            "jakarta.persistence.GeneratedValue",
            "jakarta.persistence.GenerationType",
            "jakarta.persistence.Id",
        ]
        template = "\n\n" + self.generate_id_field_template(
            field_type, field_name, id_generation, nullable, debug
        )
        insert_position = self.treesitter_lib.get_entity_field_insert_point(
            buffer_bytes, debug
        )
        new_source = self.treesitter_lib.insert_code_into_position(
            template, insert_position, buffer_bytes, debug
        )
        type_import_path = self.treesitter_lib.get_field_type_import_path(
            field_type, debug
        )
        if type_import_path is not None:
            importings.append(type_import_path)
        new_source = self.treesitter_lib.insert_import_paths_into_buffer(
            new_source, importings, debug
        )
        if debug:
            self.logging.log(
                [
                    f"buffer path: {buffer_path}\n"
                    f"field type: {field_type}\n"
                    f"field name: {field_name}\n"
                    f"id generation: {id_generation}\n"
                    f"nullable: {nullable}\n"
                    f"insert position: {insert_position}\n"
                    f"type import path: {importings[3] if len(importings) >=3 else None}\n"
                    f"generated value import path: {importings[0]}\n"
                    f"generation type import path: {importings[1]}\n"
                    f"id import path: {importings[2]}\n"
                    f"template:\n{template}\n"
                    f"buffer before:\n{buffer_bytes.decode('utf-8')}\n"
                    f"buffer after:\n{buffer_bytes.decode('utf-8')}\n"
                ],
                "debug",
            )
            self.treesitter_lib.update_buffer(
                new_source, buffer_path, False, True, True
            )
