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
    confirm_btn_hidden = false,
    next_btn_hidden = true,
    active_tab = "many_side",
    inverse_field_type = nil,
    fetch_type = "lazy",
    collection_type = "set",
    mapping_type = "unidirectional_join_column",
    owning_side_cascades = {},
    inverse_side_cascades = {},
    orphan_removal = true,
    selected_other = {},
})

local function render_main_title(subtitle)
    return n.rows(
        { flex = 0 },
        n.paragraph({
            lines = {
                n.line(n.text("Create many-to-one relationship", "String")),
            },
            align = "center",
            is_focusable = false
        }),
        n.paragraph({
            lines = {
                n.line(n.text(subtitle, "String")),
            },
            align = "center",
            is_focusable = false,
        })
    )
end

local function render_field_type_component(_signal, options)
    local data = {}
    for _, v in ipairs(options) do
        table.insert(data, n.node({ text = v.name, is_done = false, id = v.id }))
    end
    return select_one.render_component(6, "Inverse entity", data, "inverse_field_type", _signal)
end

local function render_cascade_component(_signal, signal_key)
    local data = {
        n.node({ text = "All", is_done = false, id = "all" }),
        n.node({ text = "Merge", is_done = false, id = "merge" }),
        n.node({ text = "Persist", is_done = false, id = "persist" }),
        n.node({ text = "Remove", is_done = false, id = "remove" }),
        n.node({ text = "Refresh", is_done = false, id = "refresh" }),
        n.node({ text = "Detach", is_done = false, id = "detach" }),
    }
    return select_many.render_component(
        nil,
        "Cascade type",
        data,
        _signal,
        signal_key,
        true
    )
end

local function render_mapping_component()
    local data = {
        n.node({ text = "Unidirectional JoinColumn", is_done = true, id = "unidirectional_join_column" }),
        n.node({ text = "Bidirectional JoinColumn", is_done = false, id = "bidirectional_join_column" }),
    }
    return n.tree({
        autofocus = true,
        size = 2,
        border_label = "Mapping type",
        data = data,
        on_select = function(selected_node, component)
            local tree = component:get_tree()
            for _, node in ipairs(data) do
                node.is_done = false
            end
            selected_node.is_done = true
            signal["mapping_type"] = selected_node.id
            if signal.mapping_type:get_value() == "unidirectional_join_column" then
                signal.confirm_btn_hidden = false
                signal.next_btn_hidden = true
            end
            if signal.mapping_type:get_value() == "bidirectional_join_column" then
                signal.confirm_btn_hidden = true
                signal.next_btn_hidden = false
            end
            tree:render()
        end,
        prepare_node = function(node, line, _)
            if node.is_done then
                line:append("x", "String")
            else
                line:append("◻", "Comment")
            end
            line:append(" ")
            line:append(node.text)
            return line
        end,
    })
end

local function render_fetch_component(_signal)
    local data = {
        n.node({ text = "Lazy", is_done = true, id = "lazy" }),
        n.node({ text = "Eager", is_done = false, id = "eager" }),
    }
    return select_one.render_component(nil, "Fetch type", data, "fetch_type", _signal)
end

local function render_collection_component(_signal)
    local data = { n.node({ text = "Set", is_done = true, id = "set" }),
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

local function render_confirm_button()
    return n.button({
        flex = 1,
        label = "Confirm",
        align = "center",
        global_press_key = "<C-CR>",
        padding = { top = 1 },
        on_press = function()
            -- TODO: remove print and uncomment call
            print(vim.inspect(signal:get_value()))
            -- vim.call("ManyToOneCallback", signal:get_value())
            renderer:close()
        end,
        hidden = signal.confirm_btn_hidden
    })
end

local function render_component()
    return n.tabs(
        { active_tab = signal.active_tab },
        n.tab(
            { id = "many_side" },
            n.rows(
                { flex = 0 },
                render_main_title("Many side"),
                n.gap(1),
                render_mapping_component(),
                render_field_type_component(signal, args[2]),
                render_cascade_component(signal, "owning_side_cascades"),
                render_fetch_component(signal),
                render_other_component(signal),
                n.button({
                    label = "Next",
                    align = "center",
                    global_press_key = "<C-CR>",
                    padding = { top = 1 },
                    on_press = function()
                        signal.active_tab = "one_side"
                        signal.confirm_btn_hidden = false
                        renderer:set_size({ height = 15 })
                    end,
                    hidden = signal.next_btn_hidden
                }),
                render_confirm_button()
            )
        ),
        n.tab(
            { id = "one_side" },
            n.rows(
                { flex = 0 },
                render_main_title("One side"),
                n.gap(1),
                render_cascade_component(signal, "inverse_side_cascades"),
                render_collection_component(signal),
                n.checkbox({
                    label = "Orphan removal",
                    value = signal.orphan_removal,
                    on_change = function(is_checked)
                        signal.orphan_removal = is_checked
                    end,
                }),
                n.columns(
                    { flex = 0, align = "center" },
                    n.button({
                        flex = 1,
                        label = "Previous",
                        align = "center",
                        global_press_key = "<C-CR>",
                        padding = { top = 1 },
                        on_press = function()
                            signal.active_tab = "many_side"
                            renderer:set_size({ height = 30 })
                            if signal.mapping_type:get_value() == "unidirectional_join_column" then
                                signal.confirm_btn_hidden = false
                            end
                            if signal.mapping_type:get_value() == "bidirectional_join_column" then
                                signal.confirm_btn_hidden = true
                            end
                        end,
                        hidden = signal.next_btn_hidden
                    }),
                    render_confirm_button()
                )
            )
        )
    )
end

renderer:render(render_component())
