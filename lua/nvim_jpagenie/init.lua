local M = {}

local function get_plugin_root()
	local str = debug.getinfo(1, "S").source:sub(2)
	return str:match("(.*/)lua/")
end

local plugin_root = get_plugin_root()
local venv_path = plugin_root .. "venv"

-- Check if Python 3 is available
if not vim.fn.has("python3") then
	vim.cmd("echomsg ':python3 is not available, nvim-jpagenie will not be loaded.'")
	return
end

-- Create virtual environment if it doesn't exist
if vim.fn.empty(vim.fn.glob(venv_path)) > 0 then
	vim.fn.system({ "python3", "-m", "venv", venv_path })
end

-- Install requirements if venv exists but requirements are not installed
local pip_path = venv_path .. "/bin/pip"
local requirements_path = plugin_root .. "requirements.txt"

-- TODO: check before installing?
vim.fn.system({ pip_path, "install", "-r", requirements_path })

-- Set Python host program
vim.g.python3_host_prog = vim.fn.expand(venv_path .. "/bin/python")

vim.schedule(function()
	vim.cmd("silent! UpdateRemotePlugins")
end)

-- Keymaps
vim.api.nvim_set_keymap("n", "<leader>cj", "", { noremap = true, silent = true, desc = "JPA" })
vim.api.nvim_set_keymap(
	"n",
	"<leader>cje",
	":CreateNewJPAEntity<CR>",
	{ noremap = true, silent = true, desc = "Create new JPA Entity" }
)
vim.api.nvim_set_keymap(
	"n",
	"<leader>cjj",
	":CreateJPARepository<CR>",
	{ noremap = true, silent = true, desc = "Create JPA Repository for this Entity" }
)
vim.api.nvim_set_keymap("n", "<leader>cjf", "", { noremap = true, silent = true, desc = "Entity field creation" })
vim.api.nvim_set_keymap(
	"n",
	"<leader>cjfi",
	":CreateEntityField id<CR>",
	{ noremap = true, silent = true, desc = "Create new Entity id field" }
)
vim.api.nvim_set_keymap(
	"n",
	"<leader>cjfb",
	":CreateEntityField basic<CR>",
	{ noremap = true, silent = true, desc = "Create new Entity basic field" }
)
vim.api.nvim_set_keymap(
	"n",
	"<leader>cjfe",
	":CreateEntityField enum<CR>",
	{ noremap = true, silent = true, desc = "Create Entity enum field" }
)
vim.api.nvim_set_keymap(
	"n",
	"<leader>cjr",
	"",
	{ noremap = true, silent = true, desc = "Entity relationship creation" }
)
vim.api.nvim_set_keymap(
	"n",
	"<leader>cjro",
	":CreateEntityRelationship one-to-one<CR>",
	{ noremap = true, silent = true, desc = "Create one-to-one relationship" }
)
vim.api.nvim_set_keymap(
	"n",
	"<leader>cjrn",
	":CreateEntityRelationship many-to-one<CR>",
	{ noremap = true, silent = true, desc = "Create many-to-one relationship" }
)
vim.api.nvim_set_keymap(
	"n",
	"<leader>cjrm",
	":CreateEntityRelationship many-to-many<CR>",
	{ noremap = true, silent = true, desc = "Create many-to-many relationship" }
)

M.setup = function(_) end

return M
