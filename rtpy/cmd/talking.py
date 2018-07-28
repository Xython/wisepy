from rtpy.cmd.fn_describe import describe
from rtpy.cmd.dynamic_cast import dynamic_cast
from rtpy.cmd.cmd_parser import parse
from rtpy.cmd.cmd_ast import Quote, Cmd, Pipeline
from rtpy.cmd.color import Red, Green, Blue, Yellow, Purple, LightBlue
import types
import io
from Redy.Tools.PathLib import Path
from pprint import pprint

try:
    import readline
except:
    import pyreadline as readline


class Component:
    def __init__(self, fn, name, help_doc):
        self.fn: types.FunctionType = fn  # original function
        self.name: str = name  # command name
        self.help_doc = help_doc
        self._complete = None
        self._display = None
        self._exit = None

    def __call__(self, *args, **kwargs):
        return dynamic_cast(self.fn)(*args, **kwargs)

    def completer(self, func):
        self._complete = func
        return self

    def displayer(self, func):
        self._display = func
        return self

    def exiter(self, func):
        self._exit = func
        return self

    def complete(self, partial):
        if self._complete:
            return self._complete(partial)
        return ()

    def display(self, result):
        if not self._display:
            if isinstance(result, (list, tuple, dict)):
                pprint(result)
            elif result is not None:
                print(result)
            return
        self._display(result)

    def exit(self):
        if self._exit:
            self._exit()


def _generate_options(_registered_cmds: dict, partial: str):
    line = readline.get_line_buffer()
    option: Component = next((com for cmd_name, com in _registered_cmds.items() if line.startswith(cmd_name)), None)
    if option:
        ret = option.complete(line)
        return ret

    return (each for each in _registered_cmds if each.startswith(partial))


class Talking:

    def __init__(self):
        self._registered_cmds = {}
        self._current_com = None

    @property
    def registered_cmds(self):
        return self._registered_cmds

    def __call__(self, func: types.FunctionType):
        return self.alias(func.__name__)(func)

    def alias(self, name):
        def _inner(func):
            com = Component(func, name, describe(func, name))
            self._registered_cmds[name] = com
            return com

        return _inner

    def completer(self, partial: str, state):
        options = tuple(
                option for option in _generate_options(self._registered_cmds, partial) if option.startswith(partial))

        if state < len(options):
            return options[state]
        else:
            state -= 1

    def exit(self):
        for each in self._registered_cmds.values():
            each.exit()

    def process(self, inp):
        if isinstance(inp, Pipeline):
            return self.process_pipeline(inp)
        elif isinstance(inp, Cmd):
            return self.process_cmd(inp)
        raise TypeError(type(inp))

    def process_pipeline(self, pipeline: Pipeline):
        piped = None

        # assert len(pipeline.cmds) > 1

        for each in pipeline.cmds:
            piped = self.process(each)(piped)

        return lambda arg=None: piped

    def process_cmd(self, command: Cmd):
        instruction, args, kwargs = command.inst, command.args, command.kwargs
        instruction = self.visit_arg(instruction)

        self._current_com = com = self._registered_cmds.get(instruction)

        if not com:
            raise ValueError(f'No function registered/aliased as `{instruction}`.', UserWarning)

        if kwargs and any(True for k, _ in kwargs if k == 'help'):
            return lambda this=None: com.help_doc

        args = map(self.visit_arg, args) if args else ()
        kwargs = {k: v for k, v in kwargs} if kwargs else {}

        try:
            return lambda this=None: com(this, *args, **kwargs) if this else com(*args, **kwargs)
        except Exception as e:
            print(com.help_doc)
            raise e

    def visit_arg(self, pat):
        if isinstance(pat, Quote):
            pat = pat.cmd

            if isinstance(pat, Cmd):
                return self.process_cmd(pat)()

            elif isinstance(pat, Pipeline):
                return self.process_pipeline(pat)

            raise TypeError(type(pat))

        if isinstance(pat, str):
            return pat

    def from_io(self, ios: io.BufferedReader):
        result = self.process(parse(ios.read()))()
        self._current_com.display(result)

    def from_text(self, text):
        result = self.process(parse(text))()
        self._current_com.display(result)

    def listen(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
        readline.set_completer_delims(' \t\n;/')
        try:
            while True:
                print('wd: ', Green(Path('.')))

                cmd = input('rush> ')

                if cmd == 'exit':
                    raise SystemExit

                self.from_text(cmd)
        except (SystemExit, KeyboardInterrupt):
            print('exiting...')
            self.exit()
