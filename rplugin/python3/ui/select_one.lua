local n = require("nui-components")

-- @param size number|nil: The size of the tree (optional).
-- @param label string: The label for the tree border.
-- @param data table: A list of nodes for the tree, where each node is a table containing text and id.
-- @param signal_key string: The key in the signal table to store the selected node id.
-- @param signal table: A table that stores the selected node id.
-- @param autofocus boolean|nil: If true, autofocuses the tree component (optional).
-- @param on_select_callback function|nil: A callback function triggered on node selection (optional).
-- @return table: The rendered tree component.
local function render_component(size, label, data, signal_key, signal, autofocus, on_select_callback)
	return n.tree({
		autofocus = autofocus or false,
		size = size or #data,
		border_label = label,
		data = data,
		on_select = function(selected_node, component)
			local tree = component:get_tree()
			for _, node in ipairs(data) do
				node.is_done = false
			end
			selected_node.is_done = true
			signal[signal_key] = selected_node.id
			if on_select_callback then
				on_select_callback(selected_node, signal)
			end
			tree:render()
		end,
		prepare_node = function(node, line, _)
			if node.is_done then
				line:append("◉", "String")
			else
				line:append("○", "Comment")
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
