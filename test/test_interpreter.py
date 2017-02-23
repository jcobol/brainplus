
import sys, os

sys.path.insert(0, "%s/../lib" % os.path.dirname(__file__))

import unittest
from brainplus import Interpreter

class TestInterpreter(unittest.TestCase):
    
    def test_output(self):
        def output(interpreter, c):
            self.output_called = True
            self.output_character = c
            
        self.output_called = False
        self.output_character = None
        bp = Interpreter('.', output_function=output)
        bp.run()
        self.assertEquals(self.output_called, True)
        self.assertEquals(self.output_character, 0)
        
    def test_input(self):
        def input_fn(interpreter):
            rv = self.input_values[0]
            del self.input_values[0]
            return rv
        
        self.input_values = [10,20]
        bp = Interpreter(',>,', input_function=input_fn)
        bp.run()
        self.assertEqual(bp.memory[0], 10)
        self.assertEqual(bp.memory[1], 20)
    
    def test_pointer_changes(self):
        def on_execute(interpreter, instruction):
            self.memory_pointer_log.append(interpreter.memory_pointer)
            
        self.memory_pointer_log = []
        bp = Interpreter('>><<', on_execute=on_execute)
        bp.run()
        self.assertEqual(self.memory_pointer_log, [1, 2, 1, 0])
        
    def test_memory_pointer_underflow(self):
        bp = Interpreter('<')
        bp.run()
        # do not allow memory pointer to underflow.
        # Note: I'm not sure if this strictly follows the brainf spec, but
        # I think it's more useful so that programs are less likely to operate differently
        # in different memory sizes.
        self.assertEqual(bp.memory_pointer, 0)

    def test_memory_pointer_overflow(self):
        def on_execute(interpreter, instruction):
            self.memory_pointer_log.append(interpreter.memory_pointer)
            
        self.memory_pointer_log = []
        bp = Interpreter('>><<', on_execute=on_execute)
        msize = len(bp.memory)
        bp.memory_pointer = (msize - 1) - 1
        bp.run()
        expected = [((msize - 1) - x) for x in [0, 0, 1, 2]]
        self.assertEqual(self.memory_pointer_log, expected)

    def test_memory_changes(self):
        bp = Interpreter('+>+++-')
        bp.run()
        self.assertEqual(bp.memory[0:2], [1, 2])

    def test_loop_simple(self):            
        def on_execute(interpreter, instruction):
            self.instruction_pointer_log.append(interpreter.instruction_pointer)
            
        self.instruction_pointer_log = []
        bp = Interpreter('+++[>+<-].', on_execute=on_execute)
        bp.run()
        self.assertEqual(self.instruction_pointer_log, [1,2,3,4,5,6,7,8,3,4,5,6,7,8,3,4,5,6,7,8,9,10])
        
    def test_loop_skip_with_inner(self):
        def on_execute(interpreter, instruction):
            self.instruction_pointer_log.append(interpreter.instruction_pointer)
            
        self.instruction_pointer_log = []
        # memory == 0 so loops will be skipped
        bp = Interpreter('[+[.]].', cycle_limit=100, on_execute=on_execute)
        bp.run()
        self.assertEqual(self.instruction_pointer_log, [6,7])

    def test_loop_with_inner(self):
        # increment memory so loops are not skipped
        # note: we are relying on overflow to break out
        bp = Interpreter('+[+[.+]].', cycle_limit=2000)
        bp.run()
        # compare with value that I manually verified
        self.assertEqual(bp.cycle_count, 1021)

    def test_hello_world(self):
        def output(interpreter, c):
            self.out_str = self.out_str + chr(c)
            
        self.out_str = ''
        bp = Interpreter('++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.', output_function=output)
        bp.run()
        self.assertEquals(self.out_str, 'Hello World!\n')
        
    def test_function(self):
        bp = Interpreter('a@+')
        bp.run()
        self.assertEqual(len(bp.functions), 1)
        self.assertEqual(bp.functions[0], 2)
        self.assertEqual(bp.memory[0], 1)

    def test_nested_function(self):
        bp = Interpreter('a@+b@+')
        bp.run()
        self.assertEqual(len(bp.functions), 2)
        self.assertEqual(bp.functions[0], 2)
        self.assertEqual(bp.functions[1], 5)
        self.assertEqual(bp.memory[0], 2)
        
    def test_get_source_no_functions(self):
        bp = Interpreter('.+')
        self.assertEquals(bp.source_no_functions(), '.+')
        
        bp = Interpreter('.+@-')
        self.assertEquals(bp.source_no_functions(), '.+')
        
    def test_find_functions(self):
        bp = Interpreter('+++')
        self.assertEqual(len(bp.functions), 0)
        with self.assertRaises(IndexError):
            self.assertEqual(bp.get_function(0), '')
        
        bp = Interpreter('++@..')
        self.assertEqual(len(bp.functions), 1)
        self.assertEqual(bp.get_function(0), '..')
        
        bp = Interpreter('.@....@+.+@[+].')
        self.assertEqual(len(bp.functions), 3)
        self.assertEqual(bp.get_function(0), '....')
        self.assertEqual(bp.get_function(1), '+.+')
        self.assertEqual(bp.get_function(2), '[+].')
        
    def test_set_function(self):
        # create new function
        bp = Interpreter('.')
        bp2 = bp.set_function(0, '+')
        self.assertEqual(len(bp2.functions), 1)
        bp2 = bp2.set_function(1, '-')
        self.assertEqual(len(bp2.functions), 2)
            
        bp = Interpreter('.@+')
        bp2 = bp.set_function(0, '-')
        self.assertEquals(bp2.source, '.@-')
        
    def test_empty_functions(self):
        bp = Interpreter('abcd@@@@+')
        bp.run()
        self.assertEqual(len(bp.functions), 4)
        self.assertEqual(bp.memory[0], 1)
        
    def test_missing_function(self):
        bp = Interpreter('b@+')
        bp.run()
        self.assertEqual(bp.memory[0], 0)
        
    def test_too_many_functions(self):
        source = '.'
        # only 26 letters in the alphabet, so max 26 functions
        # attempt to use 27 functions
        for x in range(0, 27):
            source = source + '@.'
        with self.assertRaises(Exception):
            bp = Interpreter(source)
            
if __name__ == '__main__':
    unittest.main()