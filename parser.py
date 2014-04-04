#!/usr/bin/env python
#
# Scanner for a calculator interpreter

import scanner as mt_scanner
import ast


class ParserError(Exception):
    """ Parser error exception.

        pos: position in the input token stream where the error occurred.
        type: bad token type
    """

    def __init__(self, pos, type):
        self.pos = pos
        self.type = type

    def __str__(self):
        return '(Found bad token %s at %d)' % (mt_scanner.TOKENS[self.type], self.pos)


class Parser(object):
    """ Implement a parser for the following grammar:
    
        Program            ::=  Command

        Command            ::=  single-Command
                            |   Command ';' single-Command

        single-Command     ::=  V-name ':=' Expression
                            |   Identifier '(' Expression ')'
                            |   if Expression then single-Command
                                   else single-Command
                            |   while Expression do single-Command
                            |   let Declaration in single-Command
                            |   begin Command end

        Expression         ::=  primary-Expression
                            |   Expression Operator primary-Expression

        primary-Expression ::=  Integer-Literal
                            |   V-name
                            |   Operator primary-Expression
                            |   '(' Expression ')'

        V-name             ::=  Identifier

        Declaration        ::=  single-Declaration
                            |   Declaration ';' single-Declaration

        single-Declaration ::=  const Identifier ~ Expression
                            |   var Identifier : Type-denoter

        Type-denoter       ::=  Identifier

        Operator           ::=  '+' | '-' | '*' | '/' | '<' | '>' | '=' | '\'

        Identifier         ::=  Letter | Identifier Letter | Identifier Digit

        Integer-Literal    ::=  Digit | Integer-Literal Digit

        Comment            ::=  ! Graphic* <eol>
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.curindex = 0
        self.curtoken = tokens[0]
    
    def parse(self):
        #self.parse_exprlines()
        e1 = self.parse_program()
        return e1

    def parse_program(self):
        """ Program  :== single-Command EOT """

        e1 = self.parse_command()
        self.token_accept(mt_scanner.TK_EOT)
        return ast.Program(e1);

    def parse_command(self):
        """ Expression          ::=  primary-Expression
                                |   Expression Operator primary-Expression
        """

        token = self.token_current()

        if(token.type == mt_scanner.TK_LET):
            comm = self.parse_let()
        elif(token.type == mt_scanner.TK_IDENTIFIER):
            comm = self.parse_identifier()
        elif(token.type == mt_scanner.TK_BEGIN):
            comm = self.parse_begin()
        elif(token.type == mt_scanner.TK_WHILE):
            self.token_accept(mt_scanner.TK_WHILE)
            exp = self.parse_expr()
            self.token_accept(mt_scanner.TK_DO)
            comm = self.parse_command()
            comm = ast.WhileCommand(exp, comm)
        elif(token.type == mt_scanner.TK_IF):
            self.token_accept(mt_scanner.TK_IF)
            exp = self.parse_expr()
            self.token_accept_any()
            comm1 = self.parse_command()
            self.token_accept_any()
            self.token_accept(mt_scanner.TK_ELSE)
            comm2 = self.parse_command()
            comm = ast.IfCommand(exp, comm1, comm2)
        else:
            raise ParserError(self.curtoken.pos, self.curtoken.type)


        return comm

    def parse_begin(self):
        self.token_accept_any()
        comm = self.parse_command()
        token = self.token_current()
        while token.type == mt_scanner.TK_SEMICOLON:
            self.token_accept_any()
            token = self.token_current()
            if token.type == mt_scanner.TK_END:
                break
            comm2 = self.parse_command()
            token = self.token_current()
            comm = ast.SequentialCommand(comm, comm2)
        self.token_accept(mt_scanner.TK_END)
        return comm

    def parse_identifier(self):
        token = self.token_current()
        vname = ast.Vname(token.val)
        self.token_accept_any()
        token = self.token_current()

        if(token.type == mt_scanner.TK_BECOMES):
            self.token_accept_any()
            e2 = self.parse_expr()
            e1 = ast.AssignCommand(vname, e2)
        elif(token.type == mt_scanner.TK_LPAREN):
            self.token_accept_any()
            e2 = self.parse_expr()
            self.token_accept(mt_scanner.TK_RPAREN)
            e1 = ast.CallCommand(vname.identifier, e2)
        else:
            raise ParserError(self.curtoken.pos, self.curtoken.type)
        return e1

    def parse_expr(self):
        e1 = self.parse_secexpr()
        token = self.token_current()
        while token.type == mt_scanner.TK_OPERATOR and token.val in ['>', '<', '=']:
            oper = token.val
            self.token_accept_any()
            e2 = self.parse_secexpr()
            token = self.token_current()
            e1 = ast.BinaryExpression(e1, oper, e2)
        return e1

    def parse_secexpr(self):
        """ SecExpr :== PriExpr (OPER_PRI PriExpr)*"""

        e1 = self.parse_tertexpr()
        token = self.token_current()
        while token.type == mt_scanner.TK_OPERATOR and token.val in ['+', '-']:
            oper = token.val
            self.token_accept_any()
            e2 = self.parse_tertexpr()
            token = self.token_current()
            e1 = ast.BinaryExpression(e1, oper, e2)
        return e1

    def parse_tertexpr(self):
        """ TertExpr :== PriExpr (OPER_PRI PriExpr)*"""

        e1 = self.parse_priexpr()
        token = self.token_current()
        while token.type == mt_scanner.TK_OPERATOR and token.val in ['*', '/', '\\']:
            oper = token.val
            self.token_accept_any()
            e2 = self.parse_priexpr()
            token = self.token_current()
            e1 = ast.BinaryExpression(e1, oper, e2)
        return e1

    def parse_priexpr(self):
        """ primary-Expression ::=  Integer-Literal
                                |   V-name
                                |   Operator primary-Expression
                                |   '(' Expression ')' 
        """

        token = self.token_current()
        if token.type == mt_scanner.TK_INTLITERAL:
            e1 = ast.IntegerExpression(token.val)
            self.token_accept_any()
        elif token.type == mt_scanner.TK_LPAREN:
            self.token_accept_any()
            e1 = self.parse_expr()
            self.token_accept(mt_scanner.TK_RPAREN)
        elif token.type == mt_scanner.TK_IDENTIFIER:
            vname = ast.Vname(token.val)
            e1 = ast.VnameExpression(vname)
            self.token_accept_any()
        else:
            raise ParserError(self.curtoken.pos, self.curtoken.type)

        return e1

    def parse_declaration(self):
        token = self.token_current()
        if(token.type == mt_scanner.TK_VAR):
            self.token_accept_any()
            decl = self.parse_var()
            self.token_accept_any()
        elif(token.type == mt_scanner.TK_CONST):
            self.token_accept_any()
            decl = self.parse_const()
        else:
            raise ParserError(self.curtoken.pos, self.curtoken.type)
        return decl



    def parse_let(self):
        self.token_accept_any()
        decl = self.parse_declaration()
        token = self.token_current()
        while token.type == mt_scanner.TK_SEMICOLON:
            self.token_accept_any()
            token = self.token_current()
            if token.type == mt_scanner.TK_IN:
                break
            decl2 = self.parse_declaration()
            token = self.token_current()
            decl = ast.SequentialDeclaration(decl, decl2)

        self.token_accept(mt_scanner.TK_IN)
        comm = self.parse_command()
        e1 = ast.LetCommand(decl, comm)

        return e1

    def parse_const(self):
        token = self.token_current()

        if(token.type == mt_scanner.TK_IDENTIFIER):
            vname = token.val
            self.token_accept_any()
            self.token_accept(mt_scanner.TK_IS)
            token = self.token_current()
            exp = self.parse_expr()
            e1 = ast.ConstDeclaration(vname, exp)
        else:
            raise ParserError(self.curtoken.pos, self.curtoken.type)

        return e1

    def parse_var(self):
        token = self.token_current()

        if(token.type == mt_scanner.TK_IDENTIFIER):
            vname = token.val
            self.token_accept_any()
            self.token_accept(mt_scanner.TK_COLON)
            token = self.token_current()
            var_type = ast.TypeDenoter(token.val)
            e1 = ast.VarDeclaration(vname, var_type)
        else:
            raise ParserError(self.curtoken.pos, self.curtoken.type)

        return e1

    def token_current(self):
        return self.curtoken
        
    def token_accept_any(self):
        # Do not increment curindex if curtoken is TK_EOT.
        if self.curtoken.type != mt_scanner.TK_EOT:
            self.curindex += 1
            self.curtoken = self.tokens[self.curindex]

    def token_accept(self, type):
        if self.curtoken.type != type:
            raise ParserError(self.curtoken.pos, self.curtoken.type)
        self.token_accept_any()


if __name__ == '__main__':
    exprs = ["""
    ! isprime
    let var x: Integer;
        var half: Integer;
        var half1: Integer;
        var half2: Integer;
        var i: Integer;
        var count: Integer;
        
    in
      begin
        getint(x);
        half := (x / 2) + 1;
        half1 := half + 1;
        half2 := half1 + 1;
        i := 2;
        count := 2;

        while i < half do
          if (x \ i) then
            i := i + 1;
          else
            i := half2;

        if (i = half) then
          putint(1);
        else
          putint(0);

      end
              """
            ]

    for exp in exprs:
        print '=============='
        print exp
        
        scanner = mt_scanner.Scanner(exp)
        
        try:
            tokens = scanner.scan()
            print tokens
        except mt_scanner.ScannerError as e:
            print e
            continue

        parser = Parser(tokens)

        try:
            tree = parser.parse()
            print tree
        except ParserError as e:
            print e
            print 'Not Parsed!'
            continue

        print 'Parsed!'
