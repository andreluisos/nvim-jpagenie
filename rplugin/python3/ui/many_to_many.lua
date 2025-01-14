local args = ...

package.path = package.path .. ";" .. args[1] .. "/?.lua"

local n = require("nui-components")

local select_many = require("select_many")

local renderer = n.create_renderer({
	width = 65,
	height = 20,
})

local signal = n.create_signal({
	confirm_btn_hidden = false,
	next_btn_hidden = true,
	active_tab = "owning_side",
	inverse_field_type = nil,
	mapping_type = "unidirectional_join_column",
	owning_side_cascades = {},
	inverse_side_cascades = {},
	inverse_side_other = { "equals_hashcode" },
})

local function render_main_title(subtitle)
	return n.rows(
		{ flex = 0 },
		n.paragraph({
			lines = {
				n.line(n.text("Create many-to-many relationship", "String")),
			},
			align = "center",
			is_focusable = false,
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
		table.insert(data, n.node({ text = v.name, type = v.type, is_done = false, id = v.id }))
	end
	return n.tree({
		size = 6,
		border_label = "Inverse Entity",
		data = data,
		on_select = function(selected_node, component)
			local tree = component:get_tree()
			for _, node in ipairs(data) do
				node.is_done = false
			end
			selected_node.is_done = true
			_signal.inverse_field_type = selected_node.type
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

local function render_cascade_component(_signal, signal_key)
	local data = {
		n.node({ text = "Merge", is_done = false, id = "merge" }),
		n.node({ text = "Persist", is_done = false, id = "persist" }),
		n.node({ text = "Refresh", is_done = false, id = "refresh" }),
		n.node({ text = "Detach", is_done = false, id = "detach" }),
	}
	return select_many.render_component(nil, "Cascade type", data, _signal, signal_key, false)
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

local function render_inverse_other_component(_signal)
	local data = {
		n.node({ text = "Generate equals() and hashCode()", is_done = true, id = "equals_hashcode" }),
	}
	return select_many.render_component(nil, "Other", data, _signal, "inverse_side_other")
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
				inverse_field_type = signal.inverse_field_type:get_value(),
				mapping_type = signal.mapping_type:get_value(),
				owning_side_cascades = signal.owning_side_cascades:get_value(),
				inverse_side_cascades = signal.inverse_side_cascades:get_value(),
				inverse_side_other = signal.inverse_side_other:get_value(),
			}
			vim.call("ManyToManyCallback", result)
			renderer:close()
		end,
		hidden = signal.confirm_btn_hidden,
	})
end

local function render_component()
	return n.tabs(
		{ active_tab = signal.active_tab },
		n.tab(
			{ id = "owning_side" },
			n.rows(
				{ flex = 0 },
				render_main_title("Owning side"),
				n.gap(1),
				render_mapping_component(),
				render_field_type_component(signal, args[2]),
				render_cascade_component(signal, "owning_side_cascades"),
				n.button({
					label = "Next",
					align = "center",
					global_press_key = "<C-CR>",
					padding = { top = 1 },
					on_press = function()
						signal.active_tab = "inverse_side"
						signal.confirm_btn_hidden = false
						renderer:set_size({ height = 5 })
					end,
					hidden = signal.next_btn_hidden,
				}),
				render_confirm_button()
			)
		),
		n.tab(
			{ id = "inverse_side" },
			n.rows(
				{ flex = 0 },
				render_main_title("Inverse side"),
				n.gap(1),
				render_cascade_component(signal, "inverse_side_cascades"),
				render_inverse_other_component(signal),
				n.columns(
					{ flex = 0 },
					n.button({
						flex = 1,
						label = "Previous",
						align = "center",
						global_press_key = "<C-CR>",
						padding = { top = 1 },
						on_press = function()
							signal.active_tab = "owning_side"
							renderer:set_size({ height = 30 })
							if signal.mapping_type:get_value() == "unidirectional_join_column" then
								signal.confirm_btn_hidden = false
							else
								signal.confirm_btn_hidden = true
							end
						end,
						hidden = signal.next_btn_hidden,
					}),
					render_confirm_button()
				)
			)
		)
	)
end

renderer:render(render_component())
