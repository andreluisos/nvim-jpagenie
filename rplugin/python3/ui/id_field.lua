local args = ...

package.path = package.path .. ";" .. args[1] .. "/?.lua"

local n = require("nui-components")

local select_many = require("select_many")

local renderer = n.create_renderer({
	width = 65,
	height = 20,
	position = {
		row = "30%",
		col = "50%",
	},
})

local signal = n.create_signal({
	field_package_path = "java.lang",
	field_type = "Long",
	field_name = "id",
	id_generation = "auto",
	id_generation_type = "none",
	generator_name = args[3] .. "__gen",
	sequence_name = args[3] .. "__seq",
	initial_value = "1",
	allocation_size = "50",
	id_generation_type_hidden = true,
	generator_name_hidden = true,
	sequence_name_hidden = true,
	initial_value_hidden = true,
	allocation_size_hidden = true,
	uuid_type_generation_type_hidden = true,
	other = { "mandatory" },
})

local function render_main_title()
	return n.rows(
		{ flex = 0 },
		n.paragraph({
			lines = {
				n.line(n.text("New id type attribute", "String")),
			},
			align = "center",
			is_focusable = false,
		})
	)
end

local function render_field_type_component(_signal, options)
	local data = {}
	for _, v in ipairs(options) do
		if v.type == "Long" then
			table.insert(
				data,
				n.node({ text = v.name, type = v.type, package_path = v.package_path, is_done = true, id = v.id })
			)
		else
			table.insert(
				data,
				n.node({ text = v.name, type = v.type, package_path = v.package_path, is_done = false, id = v.id })
			)
		end
	end
	return n.tree({
		autofocus = true,
		size = #data,
		border_label = "Type",
		data = data,
		on_select = function(selected_node, component)
			local tree = component:get_tree()
			for _, node in ipairs(data) do
				node.is_done = false
			end
			selected_node.is_done = true
			_signal.field_type = selected_node.type
			_signal.field_package_path = selected_node.package_path
			if selected_node.type == "UUID" then
				_signal.uuid_type_generation_type_hidden = false
				_signal.id_generation = "uuid"
			else
				_signal.uuid_type_generation_type_hidden = true
				_signal.id_generation = "auto"
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

local function render_other_component(_signal)
	local data = {
		n.node({ text = "Mandatory", is_done = true, id = "mandatory" }),
		n.node({ text = "Mutable", is_done = false, id = "mutable" }),
	}
	return select_many.render_component(nil, "Other", data, _signal, "other")
end

local function render_uuid_id_generation_component(_signal, _data, _title, _signal_key, _signal_hidden_key)
	return n.tree({
		autofocus = false,
		size = #_data,
		border_label = _title,
		data = _data,
		on_select = function(selected_node, component)
			local tree = component:get_tree()
			for _, node in ipairs(_data) do
				node.is_done = false
			end
			selected_node.is_done = true
			_signal[_signal_key] = selected_node.id
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
		hidden = _signal[_signal_hidden_key],
	})
end

local function render_id_generation_component(_signal, _data, _title, _signal_key, _signal_hidden_key)
	return n.tree({
		autofocus = false,
		size = #_data,
		border_label = _title,
		data = _data,
		on_select = function(selected_node, component)
			local tree = component:get_tree()
			for _, node in ipairs(_data) do
				node.is_done = false
			end
			selected_node.is_done = true
			_signal[_signal_key] = selected_node.id
			if selected_node.id == "sequence" then
				_signal.id_generation_type_hidden = false
			else
				_signal.id_generation_type_hidden = true
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
		hidden = _signal[_signal_hidden_key]:negate(),
	})
end

local function render_id_generation_type_component(_signal, _data, _title, _signal_key)
	return n.tree({
		autofocus = false,
		size = #_data,
		border_label = _title,
		data = _data,
		on_select = function(selected_node, component)
			local tree = component:get_tree()
			for _, node in ipairs(_data) do
				node.is_done = false
			end
			selected_node.is_done = true
			_signal[_signal_key] = selected_node.id
			if selected_node.id == "entity_exclusive_generation" then
				_signal["generator_name_hidden"] = false
				_signal["sequence_name_hidden"] = false
				_signal["initial_value_hidden"] = false
				_signal["allocation_size_hidden"] = false
			else
				_signal["generator_name_hidden"] = true
				_signal["sequence_name_hidden"] = true
				_signal["initial_value_hidden"] = true
				_signal["allocation_size_hidden"] = true
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
		hidden = _signal.id_generation_type_hidden,
	})
end

local function render_text_input_component(title, signal_key, signal_hidden, size)
	return n.text_input({
		flex = 1,
		size = size or 0,
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
				field_package_path = signal.field_package_path:get_value(),
				field_type = signal.field_type:get_value(),
				field_name = signal.field_name:get_value(),
				id_generation = signal.id_generation:get_value(),
				id_generation_type = signal.id_generation_type:get_value(),
				generator_name = signal.generator_name:get_value(),
				sequence_name = signal.sequence_name:get_value(),
				initial_value = signal.initial_value:get_value(),
				allocation_size = signal.allocation_size:get_value(),
				other = signal.other:get_value(),
			}
			vim.call("CreateIdEntityFieldCallback", result)
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
		render_field_type_component(signal, args[2]),
		render_text_input_component("Field name", "field_name", false, 1),
		render_uuid_id_generation_component(signal, {
			n.node({ text = "None", is_done = false, id = "none" }),
			n.node({ text = "Auto", is_done = false, id = "auto" }),
			n.node({ text = "UUID", is_done = true, id = "uuid" }),
		}, "Id generation", "id_generation", "uuid_type_generation_type_hidden"),
		render_id_generation_component(signal, {
			n.node({ text = "None", is_done = false, id = "none" }),
			n.node({ text = "Auto", is_done = true, id = "auto" }),
			n.node({ text = "Identity", is_done = false, id = "identity" }),
			n.node({ text = "Sequence", is_done = false, id = "sequence" }),
		}, "Id generation", "id_generation", "uuid_type_generation_type_hidden"),
		render_id_generation_type_component(signal, {
			n.node({ text = "None", is_done = true, id = "none" }),
			n.node({ text = "Generate exclusively for entity", is_done = false, id = "entity_exclusive_generation" }),
			n.node({ text = "Provided by ORM", is_done = false, id = "orm_provided" }),
		}, "Generation type", "id_generation_type"),
		render_text_input_component("Generator name", "generator_name", "generator_name_hidden", 1),
		render_text_input_component("Sequence name", "sequence_name", "sequence_name_hidden", 1),
		render_text_input_component("Initial value", "initial_value", "initial_value_hidden", 1),
		render_text_input_component("Allocation size", "allocation_size", "allocation_size_hidden", 1),
		render_other_component(signal),
		render_confirm_button()
	)
end

renderer:render(render_component())
