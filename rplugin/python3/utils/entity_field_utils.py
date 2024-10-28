from pathlib import Path
from typing import List, Optional

from pynvim.api.nvim import Nvim

from utils.treesitter_utils import TreesitterUtils
from utils.common_utils import CommonUtils
from utils.logging import Logging
from utils.data_types import (
    FieldTimeZoneStorage,
    FieldTemporal,
    EnumType,
    IdGeneration,
    IdGenerationType,
)


class EntityFieldUtils:
    def __init__(
        self,
        nvim: Nvim,
        java_basic_types: list[tuple],
        treesitter_utils: TreesitterUtils,
        common_utils: CommonUtils,
        logging: Logging,
    ):
        self.nvim = nvim
        self.treesitter_utils = treesitter_utils
        self.logging = logging
        self.java_basic_types = java_basic_types
        self.common_utils = common_utils
        self.importings: List[str] = []
        self.class_body_query = "(class_body) @body"

    def generate_basic_field_template(
        self,
        field_package_path: str,
        field_type: str,
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
        snaked_field_name = self.common_utils.generate_snaked_field_name(
            field_name, debug
        )
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
        column_body = self.common_utils.generate_field_column_line(
            column_params, debug
        )
        field_body = self.common_utils.generate_field_body_line(
            field_type, field_name, debug
        )
        template += column_body + "\n" + field_body + "\n\n"
        if debug:
            self.logging.log(
                [
                    f"Field package path: {field_package_path}",
                    f"Field type: {field_type}",
                    f"Field name: {field_name}",
                    f"Field lenght: {field_length}",
                    f"Field precision: {field_precision}",
                    f"Field scale: {field_scale}",
                    f"Field time zone storage: {field_time_zone_storage}",
                    f"Field temporal: {field_temporal}",
                    f"Large object: {large_object}",
                    f"Mandatory: {mandatory}",
                    f"Unique: {unique}",
                    f"Snaked field name: {snaked_field_name}",
                    f"Raw column params: {str(column_params)}",
                    f"Column body: {column_body}",
                    f"Field body: {field_body}",
                    f"Final template: {template}",
                ],
                "debug",
            )
        return template

    def generate_id_field_template(
        self,
        field_package_path: str,
        field_type: str,
        field_name: str,
        id_generation: IdGeneration,
        id_generation_type: Optional[IdGenerationType],
        generator_name: Optional[str],
        sequence_name: Optional[str],
        initial_value: Optional[int],
        allocation_size: Optional[int],
        mandatory: bool = False,
        debug: bool = False,
    ) -> str:
        snaked_field_name = self.common_utils.generate_snaked_field_name(
            field_name, debug
        )
        column_params: List[str] = [f'name = "{snaked_field_name}"']
        template = "@Id\n"
        self.importings.extend(
            [
                "jakarta.persistence.GeneratedValue",
                "jakarta.persistence.GenerationType",
                "jakarta.persistence.Id",
                field_package_path,
            ]
        )
        if mandatory:
            column_params.append("nullable = true")
        if id_generation == "sequence":
            generated_value_body = (
                f"@GeneratedValue(strategy = GenerationType.{id_generation.upper()}"
            )
            if (
                id_generation == "sequence"
                and id_generation_type == "entity_exclusive_generation"
            ):
                generated_value_body += f', generator = "{generator_name}"'
                generated_value_body += ")\n"
                sequence_generator_body = (
                    f'@SequenceGenerator(name = "{generator_name}", '
                    f'sequenceName = "{sequence_name}"'
                )
                if initial_value != 1 and initial_value is not None:
                    sequence_generator_body += f", initialValue = {initial_value}"
                if allocation_size != 50 and allocation_size is not None:
                    sequence_generator_body += f", allocationSize = {allocation_size}"
                sequence_generator_body += ")\n"
                template += generated_value_body + sequence_generator_body
        if id_generation != "none":
            template += (
                f"@GeneratedValue(strategy = GenerationType.{id_generation.upper()})\n"
            )
        column_body = self.common_utils.generate_field_column_line(
            column_params, debug
        )
        field_body = self.common_utils.generate_field_body_line(
            field_type, field_name, debug
        )
        template += column_body + "\n" + field_body + "\n\n"
        if debug:
            self.logging.log(
                [
                    f"field name: {field_name}, "
                    f"id generation: {id_generation}, mandatory: {mandatory}"
                    f"template:\n{template}"
                ],
                "debug",
            )
        return template

    def generate_enum_field_template(
        self,
        field_package_path: str,
        field_type: str,
        field_name: str,
        field_length: Optional[int],
        enum_type: EnumType = "ORDINAL",
        mandatory: bool = False,
        unique: bool = False,
        debug: bool = False,
    ) -> str:
        snaked_field_name = self.common_utils.generate_snaked_field_name(
            field_name, debug
        )
        column_params: List[str] = [f'name = "{snaked_field_name}"']
        self.importings.extend(
            [
                "jakarta.persistence.Enumerated",
                "jakarta.persistence.EnumType",
                field_package_path,
            ]
        )
        template = f"@Enumerated(EnumType.{enum_type})\n"
        if enum_type == "STRING" and field_length and field_length != 255:
            column_params.append(f"length = {field_length}")
        if mandatory:
            column_params.append("nullable = true")
        if unique:
            column_params.append("unique = true")
        column_body = self.common_utils.generate_field_column_line(
            column_params, debug
        )
        field_body = self.common_utils.generate_field_body_line(
            field_type, field_name, debug
        )
        template += column_body + "\n" + field_body + "\n\n"
        if debug:
            self.logging.log(
                [
                    f"Field package path: {field_package_path}",
                    f"Field type: {field_type}",
                    f"Field name: {field_name}",
                    f"Field lenght: {field_length}",
                    f"Enum type: {enum_type}",
                    f"Mandatory: {mandatory}",
                    f"Unique: {unique}",
                    f"Snaked field name: {snaked_field_name}",
                    f"Raw column params: {str(column_params)}",
                    f"Column body: {column_body}",
                    f"Field body: {field_body}",
                    f"Final template: {template}",
                ],
                "debug",
            )
        return template

    def create_basic_entity_field(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_package_path: str,
        field_type: str,
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
            field_type=field_type,
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
        buffer_bytes = self.common_utils.add_imports_to_buffer(
            self.importings, buffer_bytes, debug
        )
        insert_position = self.treesitter_utils.get_entity_field_insert_point(
            buffer_bytes, debug
        )
        class_body_position = self.treesitter_utils.query_node(
            self.treesitter_utils.get_node_from_bytes(buffer_bytes),
            self.class_body_query,
            debug,
        )[0][0].start_byte
        if insert_position < class_body_position:
            insert_position = class_body_position + 1
        buffer_bytes = self.treesitter_utils.insert_code_into_position(
            template, insert_position, buffer_bytes, debug
        )
        self.treesitter_utils.update_buffer(
            buffer_bytes=buffer_bytes,
            buffer_path=buffer_path,
            save=False,
            format=True,
            organize_imports=True,
        )
        if debug:
            self.logging.log(
                [
                    f"Buffer path: {buffer_path}\n"
                    f"Field package path: {field_package_path}\n"
                    f"Field type: {field_type}\n"
                    f"Field name: {field_name}\n"
                    f"Field lenght: {field_length}\n"
                    f"Mandatory: {mandatory}\n"
                    f"Unique: {unique}\n"
                    f"Template:\n{template}\n"
                    f"Buffer before:\n{buffer_bytes.decode('utf-8')}\n"
                    f"Buffer after:\n{buffer_bytes.decode('utf-8')}\n"
                ],
                "debug",
            )

    def create_enum_entity_field(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_package_path: str,
        field_type: str,
        field_name: str,
        field_length: Optional[int],
        enum_type: EnumType = "ORDINAL",
        mandatory: bool = False,
        unique: bool = False,
        debug: bool = False,
    ) -> None:
        template = "\n\n" + self.generate_enum_field_template(
            field_package_path=field_package_path + "." + field_type,
            field_type=field_type,
            field_name=field_name,
            field_length=field_length,
            enum_type=enum_type,
            mandatory=mandatory,
            unique=unique,
            debug=debug,
        )
        buffer_bytes = self.common_utils.add_imports_to_buffer(
            self.importings, buffer_bytes, debug
        )
        insert_position = self.treesitter_utils.get_entity_field_insert_point(
            buffer_bytes, debug
        )
        buffer_bytes = self.treesitter_utils.insert_code_into_position(
            template, insert_position, buffer_bytes, debug
        )
        self.treesitter_utils.update_buffer(
            buffer_bytes=buffer_bytes,
            buffer_path=buffer_path,
            save=False,
            format=True,
            organize_imports=True,
        )
        if debug:
            self.logging.log(
                [
                    f"Buffer path: {buffer_path}\n"
                    f"Field package path: {field_package_path}\n"
                    f"Field type: {field_type}\n"
                    f"Field name: {field_name}\n"
                    f"Enum type: {enum_type}\n"
                    f"Field lenght: {field_length}\n"
                    f"Mandatory: {mandatory}\n"
                    f"Unique: {unique}\n"
                    f"Template:\n{template}\n"
                    f"Buffer before:\n{buffer_bytes.decode('utf-8')}\n"
                    f"Buffer after:\n{buffer_bytes.decode('utf-8')}\n"
                ],
                "debug",
            )

    def create_id_entity_field(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_package_path: str,
        field_type: str,
        field_name: str,
        id_generation: IdGeneration,
        id_generation_type: Optional[IdGenerationType],
        generator_name: Optional[str],
        sequence_name: Optional[str],
        initial_value: Optional[int],
        allocation_size: Optional[int],
        mandatory: bool = False,
        debug: bool = False,
    ) -> None:
        template = "\n\n" + self.generate_id_field_template(
            field_package_path=field_package_path + "." + field_type,
            field_type=field_type,
            field_name=field_name,
            id_generation=id_generation,
            id_generation_type=id_generation_type,
            generator_name=generator_name,
            sequence_name=sequence_name,
            initial_value=initial_value,
            allocation_size=allocation_size,
            mandatory=mandatory,
            debug=debug,
        )
        buffer_bytes = self.common_utils.add_imports_to_buffer(
            self.importings, buffer_bytes, debug
        )
        insert_position = self.treesitter_utils.get_entity_field_insert_point(
            buffer_bytes, debug
        )
        buffer_bytes = self.treesitter_utils.insert_code_into_position(
            template, insert_position, buffer_bytes, debug
        )
        self.treesitter_utils.update_buffer(
            buffer_bytes=buffer_bytes,
            buffer_path=buffer_path,
            save=False,
            format=True,
            organize_imports=True,
        )
        if debug:
            self.logging.log(
                [
                    f"Buffer path: {buffer_path}\n"
                    f"Field package path: {field_package_path}\n"
                    f"Field type: {field_type}\n"
                    f"Field name: {field_name}\n"
                    f"Mandatory: {mandatory}\n"
                    f"Template:\n{template}\n"
                    f"Buffer before:\n{buffer_bytes.decode('utf-8')}\n"
                    f"Buffer after:\n{buffer_bytes.decode('utf-8')}\n"
                ],
                "debug",
            )
