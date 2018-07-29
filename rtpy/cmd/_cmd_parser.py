# File automatically generated by RBNF.
from rtpy.cmd.cmd_ast import *
from rbnf.bootstrap import loader as ruiko
ulang = ruiko.Language('ulang')


@ulang
class Space(ruiko.Lexer):
    @staticmethod
    def regex():
        return ['\\s+']


@ulang
class Str(ruiko.Lexer):
    @staticmethod
    def regex():
        return ["[A-Z]\\'([^\\\\\\']+|\\\\.)*?\\'|\\'([^\\\\\\']+|\\\\.)*?\\'"]


@ulang
class DoubleQuotedStr(ruiko.Lexer):
    @staticmethod
    def regex():
        return ['[A-Z]"([^\\\\"]+|\\\\.)*?"|"([^\\\\"]+|\\\\.)*?"']


@ulang
class arg(ruiko.Parser):
    @staticmethod
    def bnf():
        return ruiko.Or([
            ruiko.Bind('str', ruiko.N('Str')),
            ruiko.Bind('str', ruiko.N('DoubleQuotedStr')),
            ruiko.Bind('pat', ruiko.N('pattern')),
            ruiko.Bind('quote', ruiko.Named('quote'))
        ])

    @staticmethod
    def rewrite(state):
        ctx = state.ctx
        str = ctx.get('str')
        str = ctx.get('str')
        pat = ctx.get('pat')
        quote = ctx.get('quote')
        if str:
            return eval(str.value)
        if quote:
            return quote
        return pat.value


@ulang
class quote(ruiko.Parser):
    @staticmethod
    def bnf():
        return ruiko.And([
            ruiko.C('`'),
            ruiko.Bind('cmd', ruiko.Named('command')),
            ruiko.C('`')
        ])

    @staticmethod
    def rewrite(state):
        ctx = state.ctx
        cmd = ctx.get('cmd')
        return Quote(cmd)


@ulang
class optional(ruiko.Parser):
    @staticmethod
    def bnf():
        return ruiko.And([
            ruiko.C('--'),
            ruiko.Bind('key', ruiko.N('pattern')),
            ruiko.Seq(ruiko.Bind('value', ruiko.Named('arg')), 0, 1)
        ])

    @staticmethod
    def fail_if(tokens, state):
        ctx = state.ctx
        key = ctx.get('key')
        value = ctx.get('value')
        return key.value.isidentifier()

    @staticmethod
    def rewrite(state):
        ctx = state.ctx
        key = ctx.get('key')
        value = ctx.get('value')
        return (key.value, (value or True))


@ulang
class must(ruiko.Parser):
    @staticmethod
    def bnf():
        return ruiko.And([
            ruiko.C('-'),
            ruiko.Bind('key', ruiko.N('pattern')),
            ruiko.Bind('value', ruiko.Named('arg'))
        ])

    @staticmethod
    def fail_if(tokens, state):
        ctx = state.ctx
        key = ctx.get('key')
        value = ctx.get('value')
        return key.value.isidentifier()

    @staticmethod
    def rewrite(state):
        ctx = state.ctx
        key = ctx.get('key')
        value = ctx.get('value')
        return (key.value, (value or True))


@ulang
class command(ruiko.Parser):
    @staticmethod
    def bnf():
        return ruiko.And([
            ruiko.Bind('instruction', ruiko.Named('arg')),
            ruiko.Seq(
                ruiko.Or([
                    ruiko.Push('args', ruiko.Named('arg')),
                    ruiko.Push('kwargs', ruiko.Named('optional')),
                    ruiko.Push('kwargs', ruiko.Named('must'))
                ]), 0, -1),
            ruiko.Seq(
                ruiko.And([
                    ruiko.C('|'),
                    ruiko.Push('and_then', ruiko.Named('command'))
                ]), 0, -1)
        ])

    @staticmethod
    def rewrite(state):
        ctx = state.ctx
        instruction = ctx.get('instruction')
        args = ctx.get('args')
        kwargs = ctx.get('kwargs')
        kwargs = ctx.get('kwargs')
        and_then = ctx.get('and_then')
        ret = Cmd(instruction, args, kwargs)
        if and_then:
            ret = Pipeline((ret, *and_then))
        return ret


@ulang
class pattern(ruiko.Lexer):
    @staticmethod
    def regex():
        return ['[^`\\s]+']


ulang.ignore('Space')
ulang.build()
