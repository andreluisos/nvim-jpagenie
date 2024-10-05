local args = ...

package.path = package.path .. ";" .. args[1] .. "/?.lua"

local n = require("nui-components")

local select_one = require("select_one")

local select_many = require("select_many")

local renderer = n.create_renderer({
    width = 65,
    height = 30
})

local signal = n.create_signal({
    inverse_field_type = nil,
    fetch_type = "lazy",
    mapping_type = "unidirectional_join_column",
    selected_cascades = {},
    selected_other = {},
})

local function render_field_type_component(_signal, options)
    local data = {}
    for _, v in ipairs(options) do
        table.insert(data, n.node({ text = v.name, is_done = false, id = v.id }))
    end
    return select_one.render_component(6, "Inverse entity", data, "inverse_field_type", _signal, true)
end

local function render_cascade_component(_signal)
    local data = {
        n.node({ text = "All", is_done = false, id = "all" }),
        n.node({ text = "Persist", is_done = false, id = "persist" }),
        n.node({ text = "Merge", is_done = false, id = "merge" }),
        n.node({ text = "Remove", is_done = false, id = "remove" }),
        n.node({ text = "Refresh", is_done = false, id = "refresh" }),
        n.node({ text = "Detach", is_done = false, id = "detach" }),
    }
    return select_many.render_component(
        nil,
        "Cascade type",
        data,
        _signal,
        "selected_cascades",
        true
    )
end

local function render_mapping_component(_signal)
    local data = {
        n.node({ text = "Unidirectional JoinColumn", is_done = true, id = "unidirectional_join_column" }),
        n.node({ text = "Bidirectional JoinColumn", is_done = false, id = "bidirectional_join_column" }),
    }
    return select_one.render_component(nil, "Mapping type", data, "mapping_type", _signal)
end

local function render_fetch_component(_signal)
    local data = {
        n.node({ text = "Lazy", is_done = true, id = "lazy" }),
        n.node({ text = "Eager", is_done = false, id = "eager" }),
    }
    return select_one.render_component(nil, "Fetch type", data, "fetch_type", _signal)
end

local function render_collection_component(_signal)
    local data = {
        n.node({ text = "Set", is_done = true, id = "set" }),
        n.node({ text = "List", is_done = false, id = "list" }),
        n.node({ text = "Collection", is_done = false, id = "collection" }),
    }
    return select_one.render_component(nil, "Collection type", data, "collection_type", _signal)
end

local function render_other_component(_signal)
    local data = {
        n.node({ text = "Mandatory", is_done = false, id = "mandatory" }),
        n.node({ text = "Unique", is_done = false, id = "unique" }),
    }
    return select_many.render_component(
        nil,
        "Other",
        data,
        _signal,
        "selected_other"
    )
end

renderer:render(
    n.rows(
        n.paragraph({
            lines = {
                n.line(n.text("Create many-to-one relationship", "String")),
            },
            align = "center",
        }),
        render_field_type_component(signal, args[2]),
        render_cascade_component(signal),
        render_mapping_component(signal),
        render_fetch_component(signal),
        render_collection_component(signal),
        render_other_component(signal),
        n.button({
            label = "Confirm",
            align = "center",
            padding = { top = 1 },
            on_press = function()
                print(vim.inspect(signal:get_value()))
                vim.call("ManyToOneCallback", signal:get_value())
                renderer:close()
            end,
        })
    )
)
