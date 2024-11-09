local args = ...

package.path = package.path .. ";" .. args[1] .. "/?.lua"

local n = require("nui-components")

local renderer = n.create_renderer({
	width = 65,
	height = 20,
})

local signal = n.create_signal({
	entity_name = "NewEntity",
	entity_type = "entity",
	package_path = args[3],
	parent_entity_type = nil,
	parent_entity_package_path = nil,
	parent_entity_path = nil,
	parent_entity_hidden = false,
})

local function render_main_title()
	return n.rows(
		{ flex = 0 },
		n.paragraph({
			lines = {
				n.line(n.text("New Entity", "String")),
			},
			align = "center",
			is_focusable = false,
		})
	)
end

local function render_parent_entity_component(_signal, options)
	local data = {}
	for _, v in ipairs(options) do
		table.insert(
			data,
			n.node({ text = v.name, is_done = false, id = v.id, type = v.type, package_path = v.package_path })
		)
	end
	return n.tree({
		size = 6,
		border_label = "Parent Entity (optional)",
		data = data,
		on_select = function(selected_node, component)
			local tree = component:get_tree()
			for _, node in ipairs(data) do
				node.is_done = false
			end
			selected_node.is_done = true
			_signal.parent_entity_type = selected_node.type
			_signal.parent_entity_package_path = selected_node.package_path
			_signal.parent_entity_path = selected_node.id
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
		hidden = _signal.parent_entity_hidden,
	})
end

local function render_entity_type_component(_signal, _data)
	return n.tree({
		size = 3,
		border_label = "Entity type",
		data = _data,
		on_select = function(selected_node, component)
			local tree = component:get_tree()
			for _, node in ipairs(_data) do
				node.is_done = false
			end
			selected_node.is_done = true
			if selected_node.id == "embeddable" then
				_signal.parent_entity_hidden = true
			else
				_signal.parent_entity_hidden = false
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

local function render_text_input_component(title, signal_key, signal_hidden, autofocus)
	return n.text_input({
		size = 1,
		autofocus = autofocus or false,
		value = signal[signal_key],
		border_label = title,
		on_change = function(value, _)
			signal[signal_key] = value
		end,
		hidden = signal[signal_hidden] or false,
	})
end

local function render_confirm_button()
	return n.button({
		flex = 1,
		label = "Confirm",
		align = "center",
		global_press_key = "<C-CR>",
		padding = { top = 1 },
		on_press = function()
			local result = {
				entity_name = signal.entity_name:get_value(),
				entity_type = signal.entity_type:get_value(),
				package_path = signal.package_path:get_value(),
				parent_entity_type = signal.parent_entity_type:get_value(),
				parent_entity_package_path = signal.parent_entity_package_path:get_value(),
				parent_entity_path = signal.parent_entity_path:get_value(),
			}
			vim.call("CreateNewJpaEntityCallback", result)
			renderer:close()
		end,
		hidden = signal.confirm_btn_hidden,
	})
end

local function render_component()
	return n.rows(
		{ flex = 0 },
		render_main_title(),
		n.gap(1),
		render_text_input_component("Entity name", "entity_name", nil, true),
		render_text_input_component("Package path", "package_path", nil, false),
		render_entity_type_component(signal, {
			n.node({ text = "Entity", is_done = true, id = "entity" }),
			n.node({ text = "Embeddable", is_done = false, id = "embeddable" }),
			n.node({ text = "Mapped Superclass", is_done = false, id = "mapped_superclass" }),
		}),
		render_parent_entity_component(signal, args[2]),
		render_confirm_button()
	)
end

renderer:render(render_component())
