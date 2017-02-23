# Implementation of BrainPlus language.
# Author: John Hopkins <johnnycobol@gmail.com>
# BrainF*ck base commands:
# >   Increment the memory pointer.
# <   Decrement the memory pointer.
# +   Increment the byte at the memory pointer.
# -   Decrement the byte at the memory pointer.
# .   Output the byte at the memory pointer.
# ,   Input a byte and store it in the byte at the memory pointer.
# [   Jump forward past the matching ] if the byte at the memory pointer is zero.
# ]   Jump backward to the matching [ unless the byte at the memory pointer is zero.
# Extended commands included in BrainPlus.
# @   Exits the program or if inside a function, return to prior position in main program and restore state.
# $   Overwrites the byte in storage with the byte at the pointer.
# !   Overwrites the byte at the pointer with the byte in storage.
# a,b Call function a - z.
# 0-F Sets the value of the current memory pointer to a multiple of 16.
# *   Sets the return value of a function to the value at the current memory pointer;
#     Parent storage will get return value.

""" Known limitations with this implementation:

- input is not line-based.  it is character based.
- code must not be split across lines
"""

import sys

class Stack(object):
    def __init__(self):
        self.stack = []
        
    def push(self, thing):
        self.stack.append(thing)
        
    def pop(self):
        rv = self.stack[-1]
        del self.stack[-1]
        return rv
    
    def peek(self):
        return self.stack[-1]
    
    def is_empty(self):
        return len(self.stack) == 0

class Interpreter(object):
    def __init__(self, source, cycle_limit=0, input_function=None, output_function=None, on_execute=None):
        self.source = source
        self.max_functions = 26
        self.find_functions()
        self.stack = Stack()
        self.memory_size = 30000
        self.memory_pointer = 0
        self.instruction_pointer = 0
        self.memory = [0 for x in range(0, self.memory_size)]
        self.input_function = input_function
        self.output_function = output_function
        self.on_execute = on_execute
        self.cycle_limit = cycle_limit
        self.cycle_count = 0
        # 8-bit limit = 255. Increases past this point will overflow back to zero.
        self.max_memory_value = 255
        self.need_to_exit = False
        self.instruction_dict = {
            '.': self.instr_print,
            ',': self.instr_input,
            '>': self.instr_inc_memory_pointer,
            '<': self.instr_dec_memory_pointer,
            '+': self.instr_inc_memory,
            '-': self.instr_dec_memory,
            '[': self.instr_loop_start,
            ']': self.instr_loop_end,
            '@': self.instr_return,
        }
        # letters a..z are function calls
        for letter in range(ord('a'), ord('z') + 1):
            self.instruction_dict[chr(letter)] = self.instr_function_call
        
    """ Make a copy of the instance, replacing zero or more configuration parameters.
    """
    def clone(self, source=None, cycle_limit=None, input_function=None, output_function=None, on_execute=None):
        kwargs = {}
        if source is None:
            new_source = self.source
        else:
            new_source = source
        if cycle_limit is not None:
            kwargs['cycle_limit'] = cycle_limit
        if input_function is not None:
            kwargs['input_function'] = input_function
        if output_function is not None:
            kwargs['output_function'] = output_function
        if on_execute is not None:
            kwargs['on_execute'] = on_execute
        return Interpreter(new_source, *kwargs)
        
            
    """ Populate self.functions with the self.source string index of each BrainPlus subroutine.
    """
    def find_functions(self):
        self.functions = []
        found = self.source.find('@')
        while found >= 0:
            self.functions.append(found + 1)
            found = self.source.find('@', found + 1)
        if len(self.functions) > self.max_functions:
            raise Exception('Error: too many functions declared: %s vs. max %s' % (len(functions), self.max_functions))
            
    def get_function(self, index):
        function_start = self.functions[index]
        if index + 1 < len(self.functions):
            function_end = self.functions[index+1]
        else:
            function_end = len(self.source) + 1
        return self.source[function_start : function_end - 1]
    
    """ Return a clone with the given function replaced
    """
    def set_function(self, index, function_source):
        split_source = self.source.split('@')
        function_ctr = len(self.functions)
        # add empty functions until we have enough functions to satisfy setting
        # function at 'index'
        while function_ctr < index + 1:
            split_source.append('')
            function_ctr = function_ctr + 1
        split_source[index + 1] = function_source
        new_source = '@'.join(split_source)
        return self.clone(source=new_source)
    
    """ Return source code without functions
    """
    def source_no_functions(self):
        if len(self.functions) > 0:
            return self.source[0: self.functions[0] - 1]
        else:
            return self.source
    
    def instruction_set(self):
        return self.instruction_dict.keys()
        
    def run(self):
        while self.instruction_pointer < len(self.source) and not self.need_to_exit:
            if self.cycle_limit != 0 and self.cycle_count >= self.cycle_limit:
                print("Ending early due to cycle limit")
                break
            instruction = self.source[self.instruction_pointer]
            self.execute_instruction(instruction)
            self.cycle_count = self.cycle_count + 1
        
    def execute_instruction(self, instruction):
        self.instruction_dict[instruction](instruction=instruction)
        if self.on_execute:
            self.on_execute(self, instruction)
        
    def instr_print(self, **kwargs):
        if self.output_function:
            self.output_function(self, self.memory[self.memory_pointer])
        self.instruction_pointer = self.instruction_pointer + 1

    def instr_input(self, **kwargs):
        if self.input_function:
            self.memory[self.memory_pointer] = self.input_function(self)
        self.instruction_pointer = self.instruction_pointer + 1

    def instr_inc_memory_pointer(self, **kwargs):
        # do not allow overflow
        if self.memory_pointer < len(self.memory) - 1:
            self.memory_pointer = self.memory_pointer + 1
        self.instruction_pointer = self.instruction_pointer + 1
        
    def instr_dec_memory_pointer(self, **kwargs):
        self.memory_pointer = self.memory_pointer - 1
        if self.memory_pointer < 0:
            # do not allow underflow
            self.memory_pointer = 0
        self.instruction_pointer = self.instruction_pointer + 1
        
    def instr_inc_memory(self, **kwargs):
        if self.memory[self.memory_pointer] < self.max_memory_value:
            self.memory[self.memory_pointer] = self.memory[self.memory_pointer] + 1
        else:
            # overflow
            self.memory[self.memory_pointer] = 0
        self.instruction_pointer = self.instruction_pointer + 1
        
    def instr_dec_memory(self, **kwargs):
        if self.memory[self.memory_pointer] > 0:
            self.memory[self.memory_pointer] = self.memory[self.memory_pointer] - 1
        else:
            # underflow
            self.memory[self.memory_pointer] = self.max_memory_value
        self.instruction_pointer = self.instruction_pointer + 1
        
    """ Skip to the closing bracket, skipping any inner loops
    """
    def skip_to_loop_end(self):
        bracket_cnt = 1
        while bracket_cnt > 0 and self.instruction_pointer < len(self.source):
            self.instruction_pointer = self.instruction_pointer + 1
            instruction = self.source[self.instruction_pointer]
            if instruction == '[':
                bracket_cnt = bracket_cnt + 1
            elif instruction == ']':
                bracket_cnt = bracket_cnt - 1

    def instr_loop_start(self, **kwargs):
        if self.memory[self.memory_pointer] == 0:
            # skip to matching ], past any inner loops
            self.skip_to_loop_end()
        else:
            self.stack.push(self.instruction_pointer)
        self.instruction_pointer = self.instruction_pointer + 1
    
    def instr_loop_end(self, **kwargs):
        if True: #not self.stack.is_empty():
            # only return to start of loop if byte at memory pointer is non-zero
            instr_ptr = self.stack.pop()
            if self.memory[self.memory_pointer] != 0:
                # go back to loop start
                self.instruction_pointer = instr_ptr
            else:
                self.instruction_pointer = self.instruction_pointer + 1

    def instr_function_call(self, **kwargs):
        instruction = kwargs['instruction']
        function_no = ord(instruction) - ord('a')
        if function_no < len(self.functions):
            # call the custom brainplus function
            self.stack.push(self.instruction_pointer + 1)
            self.instruction_pointer = self.functions[function_no]
        else:
            # ignore this function call request
            # TODO - should we bail out of the program?
            self.instruction_pointer = self.instruction_pointer + 1
        
    def instr_return(self, **kwargs):
        if self.stack.is_empty():
            # exit the program
            #TODO - should exit with an exit code which BrainF spec supports.
            self.need_to_exit = True
        else:
            self.instruction_pointer = self.stack.pop()