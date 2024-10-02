local args = ...
package.path = package.path .. ";" .. args[1] .. "/?.lua"

local n = require("nui-components")
local cascades = require("cascades")
local fetch_types = require("fetch")

local renderer = n.create_renderer({
    width = 57,
    height = 25,
})

local entity_options = {}

for _, v in ipairs(args[2]) do
    table.insert(entity_options, n.option(v.name, { id = v.id }))
end

local signal = n.create_signal({
    field_type = nil,
    fetch_type = "lazy",
    cascade_persist = false,
    cascade_merge = false,
    cascade_remove = false,
    cascade_refresh = false,
    cascade_detach = false,
    unique = false,
    mandatory = false
})

renderer:render(
    n.rows(
        { flex = 1 },
        n.select({
            flex = 1,
            autofocus = true,
            border_label = "Inverse entity",
            selected = signal.field_type,
            data = entity_options,
            multiselect = false,
            on_select = function(node)
                signal.field_type = node.id
            end,
        }),
        cascades.render_component(signal),
        fetch_types.render_component(signal),
        n.checkbox({
            label = "Mandatory",
            value = signal.mandatory,
            on_change = function(is_checked)
                signal.mandatory = is_checked
            end,
        }),
        n.checkbox({
            label = "Unique",
            value = signal.unique,
            on_change = function(is_checked)
                signal.unique = is_checked
            end,
        }),
        n.gap(1),
        n.button({
            label = "Confirm",
            align = "center",
            padding = { bottom = 1 },
            on_press = function()
                vim.call("GenieCallbackFunction", signal:get_value())
                renderer:close()
            end,
        })
    )
)
