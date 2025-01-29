import json
import re
from typing import List, Dict, Optional
from tool import Tool
from base_provider import BaseProvider

class Agent:
    def __init__(self, 
                 llm_provider: BaseProvider,
                 tools: List[Tool] = [],
                 output_schema: Optional[Dict] = None,
                 max_retries: int = 3):
        self.llm = llm_provider # initialize LLM provider
        self.tools = {tool.name: tool for tool in tools} or {} # initialize tools
        self.output_schema = output_schema or {} # initialize output schema
        self.max_retries = max_retries # initialize max retries
        self.memory = []    
        self.thoughts = []
        
    def _system_prompt(self) -> str: # need to redo this prompt for better reasoning
        base = [
            "You are a reasoning agent that uses Chain of Thought and ReAct paradigm.",
            "Think step-by-step and decide if you need to use tools.",
            "Format your response according to these rules:",
            "1. Always start your thinking with 'Thought:'",
            "2. If you think that a tool is needed, write 'Action: TOOL_NAME' followed by 'Action Input: <input>'",
            "3. For final answers, use 'Final Answer:' followed by the response",
        ]
        
        if self.tools: # add tools to system prompt only if they exist
            base.append("\nAvailable Tools:")
            for tool in self.tools.values():
                base.append(f"- {tool.name}: {tool.description}")
        
        if self.output_schema: # add output schema to system prompt
            schema_str = json.dumps(self.output_schema, indent=2)
            base.append(f"\nOutput must conform to this JSON schema:\n{schema_str}")
            
        return "\n".join(base)

    def _format_history(self) -> List[Dict]:
        return [
            {"role": "system", "content": self._system_prompt()},
            *self.memory
        ]

    def _parse_response(self, response: str) -> Dict: # need to redo this for better parsing but the idea is to use regex to find thoughts, actions, action inputs, and final answers
        thought = re.findall(r'Thought:(.*?)(?:\nAction:|$)', response, re.DOTALL)
        action = re.findall(r'Action:(\w+)', response)
        action_input = re.findall(r'Action Input:(.*?)(?:\nThought:|$)', response, re.DOTALL)
        final_answer = re.findall(r'Final Answer:(.*)', response, re.DOTALL)

        return {
            'thought': thought[-1].strip() if thought else None,
            'action': action[0].strip() if action else None,
            'action_input': action_input[0].strip() if action_input else None,
            'final_answer': final_answer[0].strip() if final_answer else None
        }

    # get tool from the tools list
    def _choose_tool(self, action_name: str) -> Tool:
        return self.tools.get(action_name)

    # validate output. needs to be implemented correctly
    def _validate_output(self, output: str) -> bool:
        if not self.output_schema:
            return True
            
        try:
            json_output = json.loads(output)
            # simple validation - in real use you'd use JSON schema validator
            required_keys = self.output_schema.get('required', [])
            return all(key in json_output for key in required_keys)
        except json.JSONDecodeError:
            return False

    # run the agent. the main part of the code.
    def run(self, query: str) -> str:
        # append query to memory
        self.memory.append({"role": "user", "content": query})
        final_answer = None
        retries = 0
        
        # main loop
        while retries < self.max_retries and not final_answer:
            # generate response from messages
            messages = self._format_history()
            response = self.llm.generate(messages)
            
            # parse response
            parsed = self._parse_response(response)
            self.thoughts.append(parsed.get('thought', ''))
            
            # check if final answer is present, otherwise continue
            if parsed['final_answer']:
                # if there is an output schema, validate the output
                if self.output_schema:
                    if self._validate_output(parsed['final_answer']):
                        final_answer = parsed['final_answer']
                    else:
                        error = f"Invalid output structure. Required schema: {json.dumps(self.output_schema)}"
                        self.memory.append({"role": "assistant", "content": response})
                        self.memory.append({"role": "user", "content": error})
                        retries += 1
                else:
                    final_answer = parsed['final_answer']
            # if there is no final answer, check if there is an action
            elif parsed['action']:
                tool = self._choose_tool(parsed['action'])
                
                # if there is a tool, execute it
                if tool:
                    try:
                        action_input = json.loads(parsed['action_input'])
                        result = tool.execute(**action_input)
                        self.memory.extend([
                            {"role": "assistant", "content": response},
                            {"role": "user", "content": f"Tool Result: {result}"}
                        ])
                    except Exception as e:
                        self.memory.extend([
                            {"role": "assistant", "content": response},
                            {"role": "user", "content": f"Tool Error: {str(e)}"}
                        ])
                else:
                    self.memory.append({"role": "assistant", "content": response})
                    self.memory.append({"role": "user", "content": "Invalid tool selected"})
            else:
                self.memory.append({"role": "assistant", "content": response})
                self.memory.append({"role": "user", "content": "Please provide a valid response format"})
                retries += 1
        # return final answer
        return final_answer or "Unable to generate valid response after maximum retries"




