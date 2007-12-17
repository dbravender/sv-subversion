from nose.tools import eq_, raises
from sv.command import Commands

class TestCommand(object):
    def setup(self):
        self.commands = Commands()
    
    def test_as_decorator(self):
        @self.commands
        def one():
            '''one doc'''
            pass
        
        eq_(self.commands.help, {'one':'one doc'})
        eq_(self.commands.commands.keys(), ['one'])
    
    def test_alias(self):
        @self.commands(aliases=['two'])
        def one():
            '''one doc'''
            return 'result'
        
        eq_(self.commands.commands['two'](), self.commands.commands['one']())
        eq_(self.commands.help, {'one':'one doc', 'two': '(alias for one)'})
        eq_(set(self.commands.commands.keys()), set(['one', 'two']))
        