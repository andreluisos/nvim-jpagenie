local args = ...

package.path = package.path .. ";" .. args[1] .. "/?.lua"

local select_one = require("select_one")

local n = require("nui-components")

local renderer = n.create_renderer({
	width = 65,
	height = 15,
})

local signal = n.create_signal({
	file_name = "NewFile",
	file_type = "class",
	package_path = args[2],
})

local function render_main_title()
	return n.rows(
		{ flex = 0 },
		n.paragraph({
			lines = {
				n.line(n.text("New Java file", "String")),
			},
			align = "center",
			is_focusable = false,
		})
	)
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

local function render_file_type_component(_signal)
	local data = {
		n.node({ text = "Class", is_done = true, id = "class" }),
		n.node({ text = "Interface", is_done = false, id = "interface" }),
		n.node({ text = "Record", is_done = false, id = "record" }),
		n.node({ text = "Enum", is_done = false, id = "enum" }),
		n.node({ text = "Annotation", is_done = false, id = "annotation" }),
	}
	return select_one.render_component(nil, "File type", data, "file_type", _signal)
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
				file_name = signal.file_name:get_value(),
				file_type = signal.file_type:get_value(),
				package_path = signal.package_path:get_value(),
			}
			vim.call("CreateNewJavaFileCallback", result)
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

		render_text_input_component("File name", "file_name", nil, true),
		render_text_input_component("Package path", "package_path", nil, false),
		render_file_type_component(signal),
		render_confirm_button()
	)
end

renderer:render(render_component())
