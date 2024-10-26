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
if vim.fn.empty(vim.fn.glob(venv_path .. "/lib")) > 0 then
	vim.fn.system({ pip_path, "install", "-r", requirements_path })
end

-- Set Python host program
vim.g.python3_host_prog = vim.fn.expand(venv_path .. "/bin/python")

-- Update remote plugins
vim.cmd("silent! UpdateRemotePlugins")

M.setup = function(_) end

return M
