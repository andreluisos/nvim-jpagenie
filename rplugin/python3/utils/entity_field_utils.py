from pathlib import Path
from typing import List, Optional

from pynvim.api.nvim import Nvim
from tree_sitter import Tree

from custom_types.enum_type import EnumType
from custom_types.other import Other
from custom_types.field_time_zone_storage import FieldTimeZoneStorage
from custom_types.field_temporal import FieldTemporal
from custom_types.id_generation import IdGeneration
from custom_types.id_generation_type import IdGenerationType
from custom_types.log_level import LogLevel
from custom_types.java_file_data import JavaFileData
from custom_types.create_id_field_args import CreateIdEntityFieldArgs
from custom_types.create_basic_field_args import CreateBasicEntityFieldArgs
from custom_types.create_enum_field_args import CreateEnumEntityFieldArgs

from utils.treesitter_utils import TreesitterUtils
from utils.common_utils import CommonUtils
from utils.logging import Logging


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

    def merge_field_params(self, params: List[str], debug: bool = False) -> str:
        merged_params = ", ".join(params)
        if debug:
            self.logging.log(f"Merged params: {merged_params}", LogLevel.DEBUG)
        return ", ".join(params)

    def generate_field_column_line(self, params: List[str], debug: bool = False) -> str:
        merged_params = self.merge_field_params(params, debug)
        column_line = f"@Column({merged_params})"
        if debug:
            self.logging.log(
                [
                    f"Merged params: {merged_params}",
                    f"Column line: {column_line}",
                ],
                LogLevel.DEBUG,
            )
        return column_line

    def generate_field_body_line(
        self, field_type: str, field_name: str, debug: bool = False
    ) -> str:
        field_body_line = f"private {field_type} {field_name};"
        if debug:
            self.logging.log(
                f"Field body line: {field_body_line }",
                LogLevel.DEBUG,
            )
        return field_body_line

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
        imports_to_add: List[str] = []
        snaked_field_name = self.common_utils.convert_to_snake_case(field_name, debug)
        column_params: List[str] = [f'name = "{snaked_field_name}"']
        template = ""
        imports_to_add.append("jakarta.persistence.Column")
        if "." in field_package_path:
            imports_to_add.append(field_package_path + "." + field_type)
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
            imports_to_add.extend(
                [
                    "org.hibernate.annotations.TimeZoneStorage",
                    "org.hibernate.annotations.TimeZoneStorageType",
                ]
            )
            template += (
                f"\n\t@TimeZoneStorage(TimeZoneStorageType.{field_time_zone_storage})"
            )
        if (
            field_package_path
            in [
                "java.util.Date",
                "java.util.Calendar",
            ]
            and field_temporal is not None
        ):
            imports_to_add.extend(
                ["jakarta.persistence.Temporal", "jakarta.persistence.TemporalType"]
            )
            template += f"\n\t@Temporal(TemporalType.{field_temporal})"
        if (
            field_package_path == "java.math.BigDecimal"
            and field_precision is not None
            and field_scale is not None
        ):
            column_params.extend(
                [f"precision = {field_precision}", f"scale = {field_scale}"]
            )
        if large_object:
            imports_to_add.append("jakarta.persistence.Lob")
            template += "\n\t@Lob"
        if mandatory:
            column_params.append("nullable = true")
        if unique:
            column_params.append("unique = true")
        column_body = self.generate_field_column_line(column_params, debug)
        field_body = self.generate_field_body_line(
            field_type, self.common_utils.generate_field_name(field_name, debug), debug
        )
        template += "\n\t" + column_body + "\n\t" + field_body + "\n"
        if debug:
            self.logging.log(
                [
                    f"Snaked field name: {snaked_field_name}",
                    f"Raw column params: {str(column_params)}",
                    f"Column body: {column_body}",
                    f"Field body: {field_body}",
                    f"Final template: {template}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
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
        imports_to_add = [
            "jakarta.persistence.Column",
            "jakarta.persistence.GeneratedValue",
            "jakarta.persistence.GenerationType",
            "jakarta.persistence.Id",
            field_package_path + "." + field_type,
        ]
        snaked_field_name = self.common_utils.convert_to_snake_case(field_name, debug)
        column_params: List[str] = [f'name = "{snaked_field_name}"']
        template = "\n\t@Id\n"
        if mandatory:
            column_params.append("nullable = true")
        if id_generation == "sequence":
            generated_value_body = f"\t@GeneratedValue(strategy = GenerationType.{id_generation.value.upper()}"
            if (
                id_generation == "sequence"
                and id_generation_type == "entity_exclusive_generation"
            ):
                generated_value_body += f', generator = "{generator_name}"'
                generated_value_body += ")"
                sequence_generator_body = (
                    f'\t@SequenceGenerator(name = "{generator_name}", '
                    f'sequenceName = "{sequence_name}"'
                )
                if initial_value != 1 and initial_value is not None:
                    sequence_generator_body += f", initialValue = {initial_value}"
                if allocation_size != 50 and allocation_size is not None:
                    sequence_generator_body += f", allocationSize = {allocation_size}"
                sequence_generator_body += ")\n"
                template += generated_value_body + sequence_generator_body
        if id_generation != "none":
            template += f"\t@GeneratedValue(strategy = GenerationType.{id_generation.value.upper()})"
        column_body = self.generate_field_column_line(column_params, debug)
        field_body = self.generate_field_body_line(
            field_type, self.common_utils.generate_field_name(field_name, debug), debug
        )
        template += "\n\t" + column_body + "\n\t" + field_body + "\n"
        if debug:
            self.logging.log(
                [
                    f"Snaked field name: {snaked_field_name}",
                    f"Raw column params: {str(column_params)}",
                    f"Column body: {column_body}",
                    f"Field body: {field_body}",
                    f"Final template: {template}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return template

    def generate_enum_field_template(
        self,
        field_package_path: str,
        field_type: str,
        field_name: str,
        field_length: Optional[int],
        enum_type: EnumType = EnumType.ORDINAL,
        mandatory: bool = False,
        unique: bool = False,
        debug: bool = False,
    ) -> str:
        imports_to_add: List[str] = ["jakarta.persistence.Column"]
        snaked_field_name = self.common_utils.convert_to_snake_case(field_name, debug)
        column_params: List[str] = [f'name = "{snaked_field_name}"']
        imports_to_add.extend(
            [
                "jakarta.persistence.Enumerated",
                "jakarta.persistence.EnumType",
                field_package_path + "." + field_type,
            ]
        )
        template = f"\n\t@Enumerated({enum_type})"
        if enum_type == "STRING" and field_length and field_length != 255:
            column_params.append(f"length = {field_length}")
        if mandatory:
            column_params.append("nullable = true")
        if unique:
            column_params.append("unique = true")
        column_body = self.generate_field_column_line(column_params, debug)
        field_body = self.generate_field_body_line(
            field_type, self.common_utils.generate_field_name(field_name, debug), debug
        )
        template += "\n\t" + column_body + "\n\t" + field_body + "\n"
        if debug:
            self.logging.log(
                [
                    f"Snaked field name: {snaked_field_name}",
                    f"Raw column params: {str(column_params)}",
                    f"Column body: {column_body}",
                    f"Field body: {field_body}",
                    f"Final template: {template}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return template

    def update_buffer(
        self, buffer_tree: Tree, buffer_path: Path, template: str, debug: bool = False
    ) -> None:
        updated_buffer_tree = self.treesitter_utils.add_imports_to_file_tree(
            buffer_tree, debug
        )
        insert_byte = self.treesitter_utils.get_entity_field_insert_byte(
            updated_buffer_tree, debug
        )
        if not insert_byte:
            error_msg = "Unable to get field insert position"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        updated_buffer_tree = self.treesitter_utils.insert_code_at_position(
            template, insert_byte, updated_buffer_tree
        )
        self.treesitter_utils.update_buffer(
            tree=updated_buffer_tree, buffer_path=buffer_path, save=True, debug=debug
        )
        if debug:
            self.logging.log(
                [
                    f"Template:\n{template}\n"
                    f"Node before:\n{self.treesitter_utils.get_node_text_as_string(buffer_tree.root_node)}\n"
                    f"Node after:\n{self.treesitter_utils.get_node_text_as_string(updated_buffer_tree.root_node)}\n"
                ],
                LogLevel.DEBUG,
            )

    def create_basic_entity_field(
        self,
        buffer_file_data: JavaFileData,
        args: CreateBasicEntityFieldArgs,
        debug: bool = False,
    ) -> None:
        template = self.generate_basic_field_template(
            field_package_path=args.field_package_path,
            field_type=args.field_type,
            field_name=args.field_name,
            field_length=args.field_length,
            field_precision=args.field_precision,
            field_scale=args.field_scale,
            field_time_zone_storage=args.field_time_zone_storage_enum,
            field_temporal=args.field_temporal_enum,
            mandatory=True if Other.MANDATORY in args.other_enum else False,
            unique=True if Other.UNIQUE in args.other_enum else False,
            large_object=True if Other.LARGE_OBJECT in args.other_enum else False,
            debug=debug,
        )
        self.update_buffer(
            buffer_file_data.tree, buffer_file_data.path, template, debug
        )

    def create_enum_entity_field(
        self,
        buffer_file_data: JavaFileData,
        args: CreateEnumEntityFieldArgs,
        debug: bool = False,
    ) -> None:
        template = self.generate_enum_field_template(
            field_package_path=args.field_package_path,
            field_type=args.field_type,
            field_name=args.field_name,
            field_length=args.field_length,
            enum_type=args.enum_type_enum,
            mandatory=True if Other.MANDATORY in args.other_enum else False,
            unique=True if Other.UNIQUE in args.other_enum else False,
            debug=debug,
        )
        self.update_buffer(
            buffer_file_data.tree, buffer_file_data.path, template, debug
        )

    def create_id_entity_field(
        self,
        buffer_file_data: JavaFileData,
        args: CreateIdEntityFieldArgs,
        debug: bool = False,
    ) -> None:
        template = self.generate_id_field_template(
            field_package_path=args.field_package_path,
            field_type=args.field_type,
            field_name=args.field_name,
            id_generation=args.id_generation_enum,
            id_generation_type=args.id_generation_type_enum,
            generator_name=args.generator_name,
            sequence_name=args.sequence_name,
            initial_value=args.initial_value,
            allocation_size=args.allocation_size,
            mandatory=True if Other.MANDATORY in args.other_enum else False,
            debug=debug,
        )
        self.update_buffer(
            buffer_file_data.tree, buffer_file_data.path, template, debug
        )
