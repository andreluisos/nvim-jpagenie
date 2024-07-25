local venv_path = vim.fn.expand("./venv")

vim.g.python3_host_prog = vim.fn.expand(venv_path .. '/bin/python')

if not vim.fn.has('python3') then
    vim.cmd("echomsg ':python3 is not available, vim-find-test will not be loaded.'")
    return
end


-- Run the setup script to create venv and install dependencies if not already done
if vim.fn.empty(vim.fn.glob(venv_path)) > 0 then
    vim.fn.system("sh ./setup.sh")
end

vim.cmd('UpdateRemotePlugins')
