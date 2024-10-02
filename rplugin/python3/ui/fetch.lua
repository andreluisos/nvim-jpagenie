local n = require("nui-components")

local function render_component(signal)
    return n.select({
        flex = 1,
        border_label = "Fetch",
        selected = signal.fetch_type,
        data = {
            n.option("Lazy", { id = "lazy" }),
            n.option("Eager", { id = "eager" })
        },
        multiselect = false,
        on_select = function(node)
            signal.fetch_type = node.id
        end,
    })
end

return {
    render_component = render_component,
}
