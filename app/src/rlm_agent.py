"""RLM Agent using Strands native tools and agent loop."""
from __future__ import annotations

import textwrap
from typing import Any, Dict, Mapping, Sequence, Union

from botocore.config import Config as BotocoreConfig
from strands import Agent, tool
from strands.models import BedrockModel

ContextType = Union[str, Sequence[Any], Mapping[str, Any]]


class RLMAgent:
    """Recursive Language Model using Strands agent loop."""
    
    def __init__(
        self,
        model_name: str = "us.amazon.nova-pro-v1:0",
        sub_model_name: str = "us.amazon.nova-micro-v1:0",
        max_retries: int = 3,
        max_sub_calls: int = 50,
    ):
        self.root_model_name = model_name
        self.sub_model_name = sub_model_name
        self.max_sub_calls = max_sub_calls
        self.sub_call_count = 0
        self.repl_globals: Dict[str, Any] | None = None
        self.context: ContextType | None = None
        
        boto_config = BotocoreConfig(
            retries={"max_attempts": max_retries, "mode": "standard"},
            connect_timeout=10,
            read_timeout=300,
        )
        self.root_model = BedrockModel(
            model_id=self.root_model_name,
            boto_client_config=boto_config,
        )
        self.sub_model = BedrockModel(
            model_id=self.sub_model_name,
            boto_client_config=boto_config,
        )
    
    def __call__(self, user_query: str, context: ContextType) -> str:
        """Execute RLM with user query and long context."""
        self._reset_environment(context)
        context_summary = self._describe_context(context)
        system_prompt = self._build_system_prompt(context_summary)
        
        python_repl = self._create_python_repl_tool()
        llm_query_tool = self._create_llm_query_tool()
        
        agent = Agent(
            model=self.root_model,
            system_prompt=system_prompt,
            tools=[python_repl, llm_query_tool],
        )
        response = agent(user_query)
        return self._extract_response_text(response)
    
    def _reset_environment(self, context: ContextType) -> None:
        self.context = context
        self.sub_call_count = 0
        self.repl_globals = {
            "__builtins__": __builtins__,
            "context": self.context,
            "llm_query": self._repl_llm_query,
        }
    
    def _create_python_repl_tool(self):
        """Create Python REPL tool with persistent globals."""
        @tool
        def execute_python(code: str) -> str:
            import io
            from contextlib import redirect_stdout
            
            if self.repl_globals is None:
                return "Error: REPL environment is not initialized."
            
            buffer = io.StringIO()
            try:
                with redirect_stdout(buffer):
                    exec(code, self.repl_globals)
            except Exception as exc:  # pylint: disable=broad-except
                return f"Error: {type(exc).__name__}: {exc}"
            
            output = buffer.getvalue().rstrip()
            if not output:
                return "Code executed successfully (no output). Use print() to view state."
            lines = output.splitlines()
            if len(lines) > 100:
                return "\n".join(lines[-100:])
            return output
        
        return execute_python
    
    def _create_llm_query_tool(self):
        """Expose llm_query as a native Strands tool."""
        @tool
        def llm_query(prompt: str) -> str:
            return self._invoke_sub_model(prompt)
        
        return llm_query
    
    def _repl_llm_query(self, prompt: str) -> str:
        """Callable injected into the REPL globals."""
        return self._invoke_sub_model(prompt)
    
    def _invoke_sub_model(self, prompt: str) -> str:
        if self.sub_call_count >= self.max_sub_calls:
            return f"Error: Max sub-calls ({self.max_sub_calls}) reached"
        self.sub_call_count += 1
        
        sub_agent = Agent(model=self.sub_model)
        response = sub_agent(prompt)
        return self._extract_response_text(response)
    
    @staticmethod
    def _extract_response_text(response: Any) -> str:
        if hasattr(response, "message"):
            message = response.message
            if isinstance(message, str):
                return message
            if hasattr(message, "content"):
                content = message.content
                if isinstance(content, list):
                    return "".join(
                        block.get("text", "") if isinstance(block, dict) else str(block)
                        for block in content
                    )
                return str(content)
        return str(response)
    
    def _describe_context(self, context: ContextType) -> Dict[str, Any]:
        def _length(value: Any) -> int:
            if isinstance(value, str):
                return len(value)
            return len(str(value))
        
        if isinstance(context, str):
            lengths = [len(context)]
            context_type = "string"
        elif isinstance(context, Mapping):
            lengths = [_length(v) for v in context.values()]
            context_type = f"mapping[{len(context)}]"
        elif isinstance(context, Sequence):
            lengths = [_length(item) for item in context]
            context_type = f"sequence[{len(context)}]"
        else:
            as_str = str(context)
            lengths = [len(as_str)]
            context_type = type(context).__name__
        
        total = sum(lengths)
        sample_count = min(len(lengths), 20)
        sample_lengths = ", ".join(f"{lengths[i]:,}" for i in range(sample_count))
        if len(lengths) > sample_count:
            sample_lengths += ", ..."
        
        return {
            "type": context_type,
            "total": total,
            "chunk_lengths": sample_lengths or "n/a",
            "num_chunks": len(lengths),
        }
    
    def _build_system_prompt(self, summary: Mapping[str, Any]) -> str:
        chunks_line = summary["chunk_lengths"]
        total_length = summary["total"]
        context_type = summary["type"]
        num_chunks = summary["num_chunks"]
        
        prompt = f"""
You are tasked with answering a query with associated context. You can access, transform, and analyze this context interactively in a REPL environment that can recursively query sub-LLMs, which you are strongly encouraged to use as much as needed.

Your context is a {context_type} with {total_length:,} total characters and {num_chunks} chunk(s). Chunk lengths (characters): {chunks_line}.

The REPL environment is initialized with:
1. A `context` variable that contains the entire input. Inspect the context before answering.
2. An `llm_query(prompt)` function that lets you call a powerful sub-LLM capable of ~500K characters. Batch information into each call to keep the trajectory efficient.
3. Standard Python with persistent state across executions. Always use print() to view intermediate values.

You will only see truncated REPL outputs, so send buffers to `llm_query()` when you need semantic understanding. Build up buffers as you examine the context, and query the sub-LLM over those buffers to synthesize final answers.

When you execute Python code, wrap it inside triple backticks marked with `repl`. Example:
```repl
chunk_size = max(100000, len(context) // 20)
for start in range(0, len(context), chunk_size):
    chunk = context[start:start+chunk_size]
    answer = llm_query(f"Search for the target number inside this chunk:\\n{{{{chunk}}}}")
    print(f"Chunk {{{{start//chunk_size}}}}: {{{{answer}}}}")
```

After processing individual chunks, call `llm_query` again to aggregate:
```repl
final_answer = llm_query("Summarize the needles found so far:\\n" + "\\n".join(buffers))
print(final_answer)
```

IMPORTANT: when you finish, return the answer using FINAL(your answer) or FINAL_VAR(variable_name). Do not produce additional text with your final tag.

Think step-by-step, plan before acting, and remember that the REPL keeps state (lists, dicts, etc.) between executions. Always explicitly answer the user’s query in your final response.
"""
        return textwrap.dedent(prompt).strip()
