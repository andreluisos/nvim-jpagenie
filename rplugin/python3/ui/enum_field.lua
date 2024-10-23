local args = ...

package.path = package.path .. ";" .. args[1] .. "/?.lua"

local n = require("nui-components")

local select_many = require("select_many")

local renderer = n.create_renderer({
	width = 65,
	height = 20,
})

local signal = n.create_signal({
	field_path = nil,
	field_type = nil,
	field_name = "",
	field_package_path = nil,
	enum_type = "ORDINAL",
	field_length = "255",
	field_length_hidden = true,
	other = {},
})

local function render_main_title()
	return n.rows(
		{ flex = 0 },
		n.paragraph({
			lines = {
				n.line(n.text("New enum type attribute", "String")),
			},
			align = "center",
			is_focusable = false,
		})
	)
end

local function lowercaseFirstChar(str)
	if str == nil or str == "" then
		return str
	else
		local firstChar = string.lower(string.sub(str, 1, 1))
		local restOfString = string.sub(str, 2)
		return firstChar .. restOfString
	end
end

local function render_field_type_component(_signal, options)
	local data = {}
	for _, v in ipairs(options) do
		table.insert(
			data,
			n.node({ text = v.name, type = v.type, package_path = v.package_path, is_done = false, id = v.id })
		)
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
			_signal["field_path"] = selected_node.id
			_signal["field_type"] = selected_node.type
			_signal["field_package_path"] = selected_node.package_path
			_signal["field_name"] = lowercaseFirstChar(selected_node.type)
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

local function render_other_component(_signal)
	local data = {
		n.node({ text = "Mandatory", is_done = false, id = "mandatory" }),
		n.node({ text = "Unique", is_done = false, id = "unique" }),
	}
	return select_many.render_component(nil, "Other", data, _signal, "other")
end

local function render_custom_select_one_component(_signal, _data, _title, _signal_key, _signal_hidden_key)
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
			if selected_node.id == "STRING" then
				_signal[_signal_hidden_key] = false
			else
				_signal[_signal_hidden_key] = true
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
				field_path = signal.field_path:get_value(),
				field_package_path = signal.field_package_path:get_value(),
				field_type = signal.field_type:get_value(),
				field_name = signal.field_name:get_value(),
				enum_type = signal.enum_type:get_value(),
				field_length = signal.field_length:get_value(),
				other = signal.other:get_value(),
			}
			print(vim.inspect(result))
			vim.call("CreateEnumEntityFieldCallback", result)
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
		render_custom_select_one_component(signal, {
			n.node({ text = "ORDINAL", is_done = false, id = "ORDINAL" }),
			n.node({ text = "STRING", is_done = false, id = "STRING" }),
		}, "Enum type", "enum_type", "field_length_hidden"),
		render_text_input_component("Field name", "field_name", false, 1),
		render_text_input_component("Field length", "field_length", "field_length_hidden", 1),
		render_other_component(signal),
		render_confirm_button()
	)
end

renderer:render(render_component())
