from json import dumps
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pynvim.api import Nvim

from utils.logging import Logging


class UiUtils:

    def __init__(
        self,
        nvim: Nvim,
        logging: Logging,
    ):
        self.nvim = nvim
        self.logging = logging

    def generic_confirm_selection_window(self, options: List[str], title: str) -> str:
        options_display = "\n".join(options)
        opts = {"h": 4}
        option_selection = self.nvim.eval(
            f"quickui#confirm#open('{title}', '{options_display}', 1, '<ESC> to cancel', {dumps(opts)})"
        )
        lower_mapping_type = options[option_selection - 1].replace(" ", "_").lower()
        return lower_mapping_type

    def inverse_entity_selection_window(
        self,
        owning_side_field_type: str,
        available_entities: Dict[str, Tuple[str, Path]],
    ) -> Optional[str]:
        entity_display = [
            f"{k} ({v[0]})"
            for k, v in available_entities.items()
            if k != owning_side_field_type
        ]
        opts = {"title": "Select the associated Entity", "h": 10}
        inverse_entity_selection = self.nvim.eval(
            f"quickui#listbox#inputlist({entity_display}, {opts})"
        )
        if inverse_entity_selection == -1:
            return None
        return entity_display[inverse_entity_selection].split()[0]

    def cascade_selection_window(
        self, options: List[List[str | int]], title: str
    ) -> List[bool]:
        initial_list = options
        initial_list = [
            ["All", 0],
            ["Persist", 0],
            ["Merge", 0],
            ["Remove", 0],
            ["Refresh", 0],
            ["Detatch", 0],
        ]
        last_selection = 0
        while True:
            display_list = []
            for i in initial_list:
                if i[1] == 0:
                    display_list.append(f"[ ] {i[0]}")
                if i[1] == 1:
                    display_list.append(f"[X] {i[0]}")
            display_list += ["", "Confirm"]
            opts = {"title": title, "index": last_selection}
            selection = self.nvim.eval(
                f"quickui#listbox#inputlist({display_list}, {dumps(opts)})"
            )
            if selection == len(display_list) - 1 or selection == -1:
                break
            elif selection == len(display_list) - 2:
                continue
            elif selection == 0:
                all_enabled = True if initial_list[0][1] == 1 else False
                for i in initial_list:
                    if all_enabled:
                        i[1] = 0
                    else:
                        i[1] = 1
            else:
                if initial_list[0][1] == 1:
                    initial_list[0][1] = 0
                initial_list[selection][1] = 1 if initial_list[selection][1] == 0 else 0
            last_selection = selection
        return [True if i[1] == 1 else False for i in initial_list[1:]]
