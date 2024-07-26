local M = {}

local function get_plugin_root()
    local str = debug.getinfo(1, "S").source:sub(2)
    return str:match("(.*/)lua/")
end

local plugin_root = get_plugin_root()
local venv_path = plugin_root .. "venv"

if not vim.fn.has('python3') then
    vim.cmd("echomsg ':python3 is not available, vim-find-test will not be loaded.'")
    return
end

if vim.fn.empty(vim.fn.glob(venv_path)) > 0 then
    vim.fn.system("sh " .. plugin_root .. "setup.sh")
end

vim.g.python3_host_prog = vim.fn.expand(venv_path .. '/bin/python')

M.setup = function(_)
end


return M
