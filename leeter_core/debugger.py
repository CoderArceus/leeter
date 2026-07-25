import os
import asyncio
import re

class DebuggerWrapper:
    def __init__(self, binary_path: str, input_path: str):
        self.binary_path = binary_path
        self.input_path = input_path
        self.process = None
        self.is_windows = os.name == 'nt'

    async def start(self, breakpoints: list[int] = None):
        if self.is_windows:
            self.process = await asyncio.create_subprocess_exec(
                "gdb", "--interpreter=mi", self.binary_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await self._read_until_prompt()
            await self._send_cmd(f"-exec-arguments < {self.input_path}")
            await self._read_until_prompt()
            
            if breakpoints and len(breakpoints) > 0:
                for bp in breakpoints:
                    await self._send_cmd(f"-break-insert solution.cpp:{bp}")
                    await self._read_until_prompt()
            else:
                await self._send_cmd("-break-insert main")
                await self._read_until_prompt()
                
            await self._send_cmd("-exec-run")
            await self._read_until_prompt()
        else:
            self.process = await asyncio.create_subprocess_exec(
                "lldb", self.binary_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            # Setup LLDB
            await self._read_until_prompt()
            
            if breakpoints and len(breakpoints) > 0:
                for bp in breakpoints:
                    await self._send_cmd(f"b solution.cpp:{bp}")
                    await self._read_until_prompt()
            else:
                await self._send_cmd("b main")
                await self._read_until_prompt()
                
            await self._send_cmd(f"process launch -i {self.input_path}")
            await self._read_until_prompt()

    async def _send_cmd(self, cmd: str):
        if not self.process or not self.process.stdin:
            return
        self.process.stdin.write(f"{cmd}\n".encode())
        await self.process.stdin.drain()

    async def _read_until_prompt(self, timeout=2.0) -> str:
        """Reads from stdout until we see the debugger prompt."""
        if not self.process or not self.process.stdout:
            return ""
        
        output = []
        prompt = "(gdb) \n" if self.is_windows else "(lldb) "
        
        try:
            while True:
                # Read a chunk
                chunk = await asyncio.wait_for(self.process.stdout.read(4096), timeout=timeout)
                if not chunk:
                    break
                text = chunk.decode(errors='replace')
                output.append(text)
                
                # Check if prompt is at the end of the current buffer
                full_text = "".join(output)
                if full_text.endswith("(lldb) ") or full_text.endswith("(gdb) \n") or full_text.endswith("(gdb)\n"):
                    break
        except asyncio.TimeoutError:
            pass
            
        return "".join(output)

    async def step(self):
        if self.is_windows:
            await self._send_cmd("-exec-step")
        else:
            await self._send_cmd("thread step-over")
        await self._read_until_prompt()
        
    async def continue_execution(self):
        if self.is_windows:
            await self._send_cmd("-exec-continue")
        else:
            await self._send_cmd("process continue")
        await self._read_until_prompt()

    async def get_locals(self, watch_exprs: list[str] = None) -> dict:
        if self.is_windows:
            if watch_exprs:
                # GDB MI for evaluating multiple expressions is verbose, we can fallback to CLI print for now
                locals_dict = {}
                for expr in watch_exprs:
                    await self._send_cmd(f"print {expr}")
                    out = await self._read_until_prompt()
                    # simplistic fallback for GDB
                    locals_dict[expr] = {"type": "expr", "value": out.strip()}
                return locals_dict
            else:
                await self._send_cmd("-stack-list-variables --print-values")
                output = await self._read_until_prompt()
                return self._parse_gdb_locals(output)
        else:
            if watch_exprs:
                # 1. Fetch all locals to populate the evaluation context
                await self._send_cmd("frame variable")
                all_locals_output = await self._read_until_prompt()
                all_locals = self._parse_lldb_locals(all_locals_output)
                
                # 2. Build safe Python evaluation environment for indices
                env = {}
                for name, info in all_locals.items():
                    val = info.get("value", "").strip()
                    if val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                        env[name] = int(val)
                
                # 3. Rewrite array indices using eval()
                resolved_exprs = []
                for expr in watch_exprs:
                    resolved = expr
                    def repl(match):
                        inner = match.group(1)
                        try:
                            val = eval(inner, {"__builtins__": {}}, env)
                            return f"[{val}]"
                        except Exception as e:
                            with open('/tmp/dbg.log', 'a') as f:
                                f.write(f"EVAL ERR {inner}: {e}\n")
                            return match.group(0)
                    
                    resolved = re.sub(r'\[(.*?)\]', repl, resolved)
                    resolved_exprs.append(resolved)
                
                with open('/tmp/dbg.log', 'a') as f:
                    f.write(f"ENV: {env}\nRESOLVED: {resolved_exprs}\n")

                exprs_str = " ".join(resolved_exprs)
                await self._send_cmd(f"frame variable {exprs_str}")
                output = await self._read_until_prompt()
                parsed = self._parse_lldb_locals(output)
                
                with open('/tmp/dbg.log', 'a') as f:
                    f.write(f"LLDB_OUT:\n{output}\nPARSED:\n{parsed}\n")

                if not parsed:
                    return all_locals
                return parsed
            else:
                await self._send_cmd("frame variable")
                output = await self._read_until_prompt()
                return self._parse_lldb_locals(output)

    def _parse_lldb_locals(self, output: str) -> dict:
        locals_dict = {}
        # Example output: (int) x = 5
        # Example output: (std::string) s = "hello"
        for line in output.splitlines():
            line = line.strip()
            if not line or line == "(lldb) frame variable" or line == "(lldb)":
                continue
            
            # Simple regex to extract type, name, and value
            # e.g., (int) x = 5 or (int) nums[1] = 20
            match = re.match(r"^\((.*?)\)\s+(.*?)\s*=\s*(.*)", line)
            if match:
                var_type = match.group(1).strip()
                var_name = match.group(2).strip()
                var_val = match.group(3).strip()
                locals_dict[var_name] = {"type": var_type, "value": var_val}
            else:
                # Try without parentheses e.g. int x = 5
                match2 = re.match(r"^([a-zA-Z0-9_:]+)\s+(.*?)\s*=\s*(.*)", line)
                if match2:
                    var_type = match2.group(1).strip()
                    var_name = match2.group(2).strip()
                    var_val = match2.group(3).strip()
                    locals_dict[var_name] = {"type": var_type, "value": var_val}
        
        return locals_dict

    def _parse_gdb_locals(self, output: str) -> dict:
        locals_dict = {}
        # MI output parsing can be tricky, doing a best effort based on --print-values
        # Output looks like: ^done,variables=[{name="x",value="5"},{name="y",value="10"}]
        match = re.search(r'variables=\[(.*?)\]', output)
        if match:
            vars_str = match.group(1)
            # Find all name="...",value="..."
            var_matches = re.findall(r'name="(.*?)",value="(.*?)"', vars_str)
            for var_name, var_val in var_matches:
                locals_dict[var_name] = {"type": "unknown", "value": var_val}
        return locals_dict

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass
