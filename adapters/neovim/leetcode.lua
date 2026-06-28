local M = {}

-- Run leetcode <cmd> in a floating terminal window
local function run(cmd, args)
  args = args or {}
  local full_cmd = "python3 cli/leetcode.py " .. cmd .. " --problem " .. vim.fn.expand('%:p:h') .. " " .. table.concat(args, " ")

  local buf = vim.api.nvim_create_buf(false, true)
  local width  = math.floor(vim.o.columns * 0.8)
  local height = math.floor(vim.o.lines * 0.7)
  vim.api.nvim_open_win(buf, true, {
    relative = "editor",
    width    = width,
    height   = height,
    col      = math.floor((vim.o.columns - width) / 2),
    row      = math.floor((vim.o.lines - height) / 2),
    style    = "minimal",
    border   = "rounded",
    title    = " " .. full_cmd .. " ",
  })

  vim.fn.termopen(full_cmd, {
    on_exit = function(_, code)
      if code == 0 then
        vim.api.nvim_buf_set_option(buf, "modifiable", true)
        vim.api.nvim_buf_set_lines(buf, -1, -1, false, { "", "  Press q to close" })
        vim.api.nvim_buf_set_option(buf, "modifiable", false)
      end
    end
  })

  vim.keymap.set("n", "q", "<cmd>close<cr>", { buffer = buf })
end

-- Run with --json and push failures into vim.diagnostic
local function run_with_diagnostics()
  local result = vim.fn.system("python3 cli/leetcode.py run --json --problem " .. vim.fn.expand('%:p:h'))
  local ok, data = pcall(vim.json.decode, result)
  if not ok or data.status == "error" then return run("run") end

  local diagnostics = {}
  for _, case in ipairs(data.payload.cases or {}) do
    if case.status == "fail" then
      table.insert(diagnostics, {
        lnum     = 0,
        col      = 0,
        severity = vim.diagnostic.severity.ERROR,
        message  = string.format(
          "Case %d failed\n  expected: %s\n  got:      %s",
          case.index, case.expected, case.got
        ),
        source = "leetcode",
      })
    end
  end

  local bufnr = vim.api.nvim_get_current_buf()
  local ns    = vim.api.nvim_create_namespace("leetcode")
  vim.diagnostic.set(ns, bufnr, diagnostics)

  if #diagnostics == 0 then
    vim.notify(
      string.format("✓ %d/%d passed", data.payload.stats.passed, data.payload.stats.total),
      vim.log.levels.INFO
    )
  end
end

-- Keybindings (set in your init.lua with M.setup())
function M.setup(opts)
  opts = opts or {}
  local prefix = opts.prefix or "<leader>l"

  vim.keymap.set("n", prefix .. "r", run_with_diagnostics,          { desc = "LeetCode: Run" })
  vim.keymap.set("n", prefix .. "g", function() run("gen") end,     { desc = "LeetCode: Generate Driver" })
  vim.keymap.set("n", prefix .. "b", function() run("bench") end,   { desc = "LeetCode: Bench" })
  vim.keymap.set("n", prefix .. "s", function() run("stress") end,  { desc = "LeetCode: Stress Test" })
  vim.keymap.set("n", prefix .. "p", function() run("replay") end,  { desc = "LeetCode: Replay" })
  vim.keymap.set("n", prefix .. "v", function() run("paste") end,   { desc = "LeetCode: Paste to input.txt" })
  vim.keymap.set("n", prefix .. "n", function()
    local id = vim.fn.input("Problem ID: ")
    if id ~= "" then run("fetch", { id }) end
  end, { desc = "LeetCode: Fetch" })
end

return M
