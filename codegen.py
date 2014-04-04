# codegen.py - Code Generator for Mini Triangle

from byteplay import *
from types import CodeType, FunctionType
import pprint
import struct
import time
import marshal
import sys

import scanner
import parser
import ast

class CodeGenError(Exception):
    """ Code Generator Error """

    def __init__(self, ast):
        self.ast = ast

    def __str__(self):
        return 'Error at ast node: %s' % (str(self.ast))

class CodeGen(object):

    def __init__(self, tree):
        self.tree = tree
        self.code = []
        self.env = {}

    def generate(self):

        if type(self.tree) is not ast.Program:
            raise CodeGenError(self.tree)

        self.gen_command(self.tree.command)

        self.code.append((RETURN_VALUE, None))

        pprint.pprint(self.code)

        code_obj = Code(self.code, [], [], False, False, False, 'gencode', '', 0, '')
        code = code_obj.to_code()
        func = FunctionType(code, globals(), 'gencode')
        return func

    def gen_command(self, tree):

        if type(tree) is ast.AssignCommand:
            self.gen_assigncommand(tree)
        elif type(tree) is ast.CallCommand:
            self.gen_callcommand(tree)
        elif type(tree) is ast.SequentialCommand:
            self.gen_command(tree.command1)
            self.gen_command(tree.command2)
        elif type(tree) is ast.IfCommand:
            self.gen_ifcommand(tree)
        elif type(tree) is ast.WhileCommand:
            self.gen_whilecommand(tree)
        elif type(tree) is ast.LetCommand:
            self.gen_declaration(tree.declaration)
            self.gen_command(tree.command)
        else:
            raise CodeGenError(tree)

    def gen_assigncommand(self, tree):
        self.gen_expr(tree.expression)
        self.code.append((STORE_FAST, tree.variable.identifier))

    def gen_callcommand(self, tree):
        if tree.identifier == "getint":
            self.code.append((LOAD_GLOBAL, "input"))
            self.code.append((CALL_FUNCTION, 0))
            self.code.append((STORE_FAST, tree.expression.variable.identifier))
        elif tree.identifier == "putint":
            if type(tree.expression) is ast.VnameExpression:
                self.code.append((LOAD_FAST, tree.expression.variable.identifier))
            elif type(tree.expression) is ast.IntegerExpression:
                self.code.append((LOAD_CONST, tree.expression.value))
            else:
                raise CodeGenError(tree.expression)
            self.code.append((PRINT_ITEM, None))
            self.code.append((PRINT_NEWLINE, None))
            self.code.append((LOAD_CONST, 0))

    def gen_ifcommand(self, tree):
        l1 = Label()
        l2 = Label()
        l3 = Label()
        self.gen_expr(tree.expression)
        self.code.append((POP_JUMP_IF_FALSE, l1))
        self.gen_command(tree.command1)
        self.code.append((JUMP_ABSOLUTE, l2))
        self.code.append((l1, None))
        self.gen_command(tree.command2)
        self.code.append((l2, None))

    def gen_whilecommand(self, tree):
        l1 = Label()
        l2 = Label()
        l3 = Label()
        self.code.append((l1, None))
        self.gen_expr(tree.expression)
        self.code.append((POP_JUMP_IF_FALSE, l2))
        self.gen_command(tree.command)
        self.code.append((JUMP_ABSOLUTE, l1))
        self.code.append((l2, None))


    def gen_expr(self, tree):
        if type(tree) is ast.IntegerExpression:
            self.code.append((LOAD_CONST, tree.value))
        elif type(tree) is ast.VnameExpression:
            self.code.append((LOAD_FAST, tree.variable.identifier))
        elif type(tree) is ast.BinaryExpression:
            self.gen_binaryexpr(tree)
        else:
            raise CodeGenError(tree)

    def gen_binaryexpr(self, tree):
        self.gen_expr(tree.expr1)
        self.gen_expr(tree.expr2)
        op = tree.oper
        if op == '+':
            self.code.append((BINARY_ADD, None))
        elif op == '-':
            self.code.append((BINARY_SUBTRACT, None))
        elif op == '*':
            self.code.append((BINARY_MULTIPLY, None))
        elif op == '/':
            self.code.append((BINARY_DIVIDE, None))
        elif op == '>':
            self.code.append((COMPARE_OP, '>'))
        elif op == '<':
            self.code.append((COMPARE_OP, '<'))
        elif op == '=':
            self.code.append((COMPARE_OP, '=='))
        elif op == '\\':
            self.code.append((BINARY_MODULO, None))
        else:
            raise CodeGenError(op)

    def gen_declaration(self, tree):
        if type(tree) is ast.ConstDeclaration:
            self.gen_constdecl(tree)
        elif type(tree) is ast.VarDeclaration:
            self.gen_vardecl(tree)
        elif type(tree) is ast.SequentialDeclaration:
            self.gen_declaration(tree.decl1)
            self.gen_declaration(tree.decl2)
        else:
            raise CodeGenError(tree)

    def gen_constdecl(self, tree):
        self.gen_expr(tree.expression)
        self.code.append((STORE_FAST, tree.identifier))

    def gen_vardecl(self, tree):
        pass
        # self.code.append((LOAD_CONST, tree.type_denoter.identifier))
        # self.code.append((STORE_FAST, tree.identifier))






if __name__ == '__main__':
    progs = [ """let
                   var x: Integer;
                   var y: Integer;
                   var z: Integer
                 in
                   begin
                     getint(x);
                     y := 2;
                     z := x + y;
                     putint(z)
                   end
              """,
              """! Factorial
let var x: Integer;
   var fact: Integer
in
  begin
    getint(x);
    if x = 0 then
      putint(1)
    else
      begin
        fact := 1;
        while x > 0 do
          begin
            fact := fact * x;
            x := x - 1
          end;
        putint(fact)
      end
  end

              """]

    arg = sys.argv[1]

    f = open(arg, 'r')
    prog = f.read()
    print '=============='
    print prog
    
    scanner_obj = scanner.Scanner(prog)
    
    try:
        tokens = scanner_obj.scan()
        print tokens
    except scanner.ScannerError as e:
        print e
        

    parser_obj = parser.Parser(tokens)

    try:
        tree = parser_obj.parse()
        print tree
    except parser.ParserError as e:
        print e
        print 'Not Parsed!'
        

    cg = CodeGen(tree)
    code = cg.generate()
    # print code()

    # write code to file
    arg = arg.split('.')
    name = arg[0]
    pyc_file = name + '.pyc'
    print pyc_file

    with open(pyc_file,'wb') as pyc_f:
        magic = 0x03f30d0a
        pyc_f.write(struct.pack(">L",magic))
        pyc_f.write(struct.pack(">L",time.time()))
        marshal.dump(code.func_code, pyc_f)
