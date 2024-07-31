from pathlib import Path

from pynvim.api.nvim import Nvim

from coreutils import Util
from echomsg import EchoMsg


class CreateJpaEntity:
    def __init__(self, nvim: Nvim, util: Util, echomsg: EchoMsg):
        self.nvim = nvim
        self.util = util
        self.echomsg = echomsg

    def create_jpa_entity_for_buffer(self) -> None:
        current_buffer = self.nvim.current.buffer.name
        node = self.util.get_node_from_path(Path(current_buffer))
        field_declaration_query = """
        (field_declaration
            (modifiers
                (annotation
                name: (identifier) @annotation_name
                )
            )
        )
        """
        id_field_annotation_query = """
        (modifiers
            (marker_annotation
                name: (identifier) @annotation_name
            )
        )
        """
        class_annotation_query = """
        (class_declaration
            (modifiers
                (marker_annotation
                name: (identifier) @annotation_name
                )
            )
        )
        """
        results = self.util.query_node(node, class_annotation_query, debugger=True)
        buffer_is_entity = self.util.query_results_has_term(
            results, "Entity", debugger=True
        )
        if not buffer_is_entity:
            return
        results = self.util.query_node(node, id_field_annotation_query, debugger=True)
        id_annotation_found = self.util.query_results_has_term(
            results, "Id", debugger=True
        )
        if not id_annotation_found:
            superclass_query = """
            (superclass
                (type_identifier) @superclass_name
            )
            """
            results = self.util.query_node(node, superclass_query, debugger=True)
            if len(results) == 0:
                return
            super_class_name = self.util.get_node_text(results[0][0], debugger=True)
            root_path = self.util.spring_project_root_path
            if root_path is None:
                return
            class_name_query = """
            (class_declaration
                name: (identifier) @class_name
            )
            """
            for p in Path(root_path).rglob("*.java"):
                _node = self.util.get_node_from_path(p, debugger=True)
                _results = self.util.query_node(_node, class_name_query, debugger=True)
                if len(_results) == 0:
                    continue
                super_class_found = self.util.get_node_text(
                    _results[0][0], debugger=True
                )
                if super_class_found != super_class_name:
                    continue
                _results = self.util.query_node(_node, id_field_annotation_query)
                id_annotation_found = self.util.query_results_has_term(
                    _results, "Id", debugger=True
                )
                if not id_annotation_found:
                    return
                field_declaration_type_query = """
                (field_declaration
                    (modifiers
                        (marker_annotation
                        name: (identifier) @annotation_name
                        )
                    )
                    type: (type_identifier) @type_name
                    )
                """
                _results = self.util.query_node(
                    _node, field_declaration_type_query, debugger=True
                )
                for index, result in enumerate(_results):
                    self.util.get_node_text(result[0])
                    if self.util.query_results_has_term([result], "Id", debugger=True):
                        test_query = """
                        (field_declaration
                            type: (type_identifier) @type_name
                        )
                        """
                        self.util.find_type_in_node(
                            result[0], "type_identifier", debugger=True
                        )
                        # field_declaration_node = self.util.query_node(
                        #     _results[index][0], test_query, debugger=True
                        # )
                        pass
                    break
                break
