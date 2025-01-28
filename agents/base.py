from typing import Any, Dict, List
from pydantic import BaseModel, Field, ValidationError
from abc import ABC, abstractmethod
from utilities.schemas import StructuredResponse
from tools.base import BaseTool, ToolInput
from memory.base import BaseMemory
from tools.tool_registry import ToolRegistry
from utilities.async_utils import AsyncExecutor
import logging
import time
from providers.base import BaseProvider
from providers.openai_provider import OpenAIProvider
from memory.short_term import ShortTermMemory

class AgentConfig(BaseModel):
    name: str = Field(default="BasicAgent", description="Unique identifier for the agent")
    description: str = Field(default="General purpose autonomous agent", description="Agent's purpose and capabilities")
    max_retries: int = Field(default=3, ge=0, le=5, description="Maximum retries for failed operations")
    reflection: bool = Field(default=True, description="Enable self-reflection after task execution")
    timeout: float = Field(default=30.0, description="Maximum execution time in seconds")
    tools_list: List[str] = Field(default_factory=list,description="List of allowed tools (empty for all)")
    strict: bool = Field(default=True, description="Enforce strict output validation")

    
# abstract base class for autonomous agents with full lifecycle management
class Agent(ABC):
    def __init__(
        self,
        provider: BaseProvider,
        tools: ToolRegistry,
        memory: BaseMemory,
        config: AgentConfig = AgentConfig(),
    ):
        self.provider = provider # initialize LLM (need to write code for this. start with OpenAI API)
        self.tools = tools # initialize tool registry
        self.memory = memory # initialize memory
        self.config = config # initialize config
        self.metrics: Dict[str, Any] = { # metric used to track agent performance
            'tasks_completed': 0,
            'total_steps': 0,
            'average_time': 0.0
        }
        
        # hooks are for logging purpose. especially to showcase it to the user.
        self.pre_run_hooks = []
        self.post_run_hooks = []

    def validate_step(self, step: Dict) -> bool:
        required_keys = {'action', 'parameters', 'reason'}
        return all(key in step for key in required_keys)
    
    async def execute_step(self, step: Dict) -> Dict:
        for attempt in range(self.config.max_retries + 1):
            try:
                if not self.validate_step(step):
                    raise ValueError(f"Invalid step: {step}")    
                tool = self.tools.get_tool(step['action'])
                if not tool:
                    raise ValueError(f"Tool not found: {step['action']}")
                if self.tool_list and step['action'] not in self.tool_list:
                    raise ValueError(f"Tool not allowed: {step['action']}")
                context = self.memory.retrieve(step['parameters'].get('query', ''))
                tool_input = ToolInput(
                    parameters=step['parameters'],
                    context=context
                )
                
                if isinstance(tool, AsyncExecutor):
                    result = await tool.execute(tool_input)
                else:
                    result = tool.execute(tool_input)
                
                # validate tool output
                if self.config.strict_validation:
                    self.validate_tool_output(tool, result)
                
                return result
            
            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}")
                if attempt == self.config.max_retries:
                    return {
                        'error': f"Failed after {self.config.max_retries} retries",
                        'exception': str(e)
                    }
                time.sleep(1 * attempt)  # Exponential backoff
                
                
    def validate_tool_output(self, tool: BaseTool, output: Any):
        if tool.output_schema:
            try:
                tool.output_schema.validate(output)
            except ValidationError as e:
                logger.error(f"Tool output validation failed: {str(e)}")
                raise

    # this is where the llm gives a response. now i also need to make the case for non-structured output
    def plan(self, task: str) -> List[Dict]:
        prompt = f"""
        Given the task: {task}
        Available tools: {', '.join(self.tools.list_tools().keys())}
        Generate a step-by-step plan in JSON format.
        """
        
        try:
            raw_plan = self.provider.generate_response(
                prompt=prompt,
                output_model=List[Dict],
                schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string"},
                            "parameters": {"type": "object"},
                            "reason": {"type": "string"}
                        }
                    }
                }
            )
            
            return [step for step in raw_plan if self.validate_step(step)]
            
        except Exception as e:
            logger.error(f"Planning failed: {str(e)}")
            return []

    async def run(self, task: str) -> StructuredResponse:
        start_time = time.time()
        try:
            # pre execution phase
            self.memory.add({'type': 'task_start', 'content': task})
            await self._run_hooks('pre_run', task)
            
            # planning phase
            plan = self.plan(task)
            if not plan:
                raise ValueError("Failed to generate valid execution plan")
            
            # execution phase
            results = []
            for step in plan:
                step_result = await self.execute_step(step)
                results.append(step_result)
                
                # update memory and metrics
                self.memory.add({
                    'step': step['action'],
                    'result': step_result,
                    'timestamp': time.time()
                })
                self.metrics['total_steps'] += 1
                
                # early exit if needed
                if 'error' in step_result:
                    break
            
            # post execution phase
            if self.config.enable_reflection:
                reflection = self.reflect(results)
                self.memory.add({'type': 'reflection', 'content': reflection})
            
            # update metrics
            exec_time = time.time() - start_time
            self.metrics['tasks_completed'] += 1
            self.metrics['average_time'] = (
                (self.metrics['average_time'] * (self.metrics['tasks_completed'] - 1) + exec_time) / self.metrics['tasks_completed']
            )
            
            # return results with metadata
            return StructuredResponse(
                success=True,
                data={'results': results},
                metadata={
                    'execution_time': exec_time,
                    'steps_executed': len(results),
                    'agent_config': self.config.dict()
                }
            )
            
        except Exception as e:
            logger.exception("Critical error during execution")
            return StructuredResponse(
                success=False,
                data={},
                errors=[str(e)],
                metadata={'execution_time': time.time() - start_time}
            )
            
        finally:
            await self._run_hooks('post_run', task)
            self.memory.add({'type': 'task_end', 'content': task})

    def reflect(self, results: List[Dict]) -> str:
        reflection_prompt = f"""
        Analyze this execution trace and suggest improvements:
        {results}
        
        Consider:
        - Tool selection effectiveness
        - Parameter tuning
        - Error patterns
        - Alternative approaches
        """
        
        return self.llm.generate(reflection_prompt)

    async def _run_hooks(self, hook_type: str, task: str):
        for hook in getattr(self, f"{hook_type}_hooks", []):
            try:
                if callable(hook):
                    await hook(self, task)
            except Exception as e:
                logger.error(f"Hook {hook.__name__} failed: {str(e)}")

    def add_hook(self, hook_type: str, callback: callable):
        if hook_type == 'pre_run':
            self.pre_run_hooks.append(callback)
        elif hook_type == 'post_run':
            self.post_run_hooks.append(callback)

    def validate_output(self, output: Dict) -> bool:
        try:
            StructuredResponse(**output)
            return True
        except ValidationError as e:
            logger.error(f"Output validation failed: {str(e)}")
            return False

    def __repr__(self):
        return f"<Agent {self.config.name} | Tools: {len(self.tools.list_tools())} | Memory: {len(self.memory)}>"
