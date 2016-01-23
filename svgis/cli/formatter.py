import argparse


class CommandHelpFormatter(argparse.RawDescriptionHelpFormatter):

    def format_action(self, action):
        parts = super(CommandHelpFormatter, self)._format_action(action)
        if action.nargs == argparse.PARSER:
            parts = "\n".join(parts.split("\n")[1:])
        return parts


class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):

    def format_action_invocation(self, action):
        sup = super(SubcommandHelpFormatter, self)

        if not action.option_strings:
            default = action.dest
            metavar, = sup._metavar_formatter(action, default)(1)
            return metavar

        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)
            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            else:
                default = action.dest
                args_string = self._format_args(action, default)
                for option_string in action.option_strings[:-1]:
                    parts.append('%s' % (option_string))
                parts.append('%s %s' % (action.option_strings[-1], args_string))

            return ', '.join(parts)
