local n = require("nui-components")

local function render_component(signal)
    return n.tree({
        border_label = "Cascades",
        flex = 1,
        data = {
            n.node({ text = "Persist", is_done = signal.cascade_persist }),
            n.node({ text = "Merge", is_done = signal.cascade_merge }),
            n.node({ text = "Remove", is_done = signal.cascade_remove }),
            n.node({ text = "Refresh", is_done = signal.cascade_refresh }),
            n.node({ text = "Detach", is_done = signal.cascade_detach }),
        },
        on_select = function(node, component)
            local tree = component:get_tree()
            if node.text == "Persist" then
                signal.cascade_persist = not node.is_done
            elseif node.text == "Merge" then
                signal.cascade_merge = not node.is_done
            elseif node.text == "Remove" then
                signal.cascade_remove = not node.is_done
            elseif node.text == "Refresh" then
                signal.cascade_refresh = not node.is_done
            elseif node.text == "Detach" then
                signal.cascade_detach = not node.is_done
            end
            node.is_done = not node.is_done
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

return {
    render_component = render_component,
}
