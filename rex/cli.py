
import argparse
import sys
from .interpreter import RexInterpreter, RexError
from . import __version__

def main():
    parser = argparse.ArgumentParser(prog='rex', description='Rex Lang — Made in Mzansi 🇿🇦')
    parser.add_argument('command', nargs='?', default='run', help='run')
    parser.add_argument('file', nargs='?', help='.rex file to run')
    parser.add_argument('--version', action='store_true', help='show version')
    args = parser.parse_args()

    if args.version:
        print(f"Rex {__version__}")
        return 0

    if args.command == 'run' and args.file:
        interp = RexInterpreter()
        try:
            interp.run_file(args.file)
            return 0
        except RexError as e:
            print(f"Rex Error: {e}", file=sys.stderr)
            return 1
        except FileNotFoundError:
            print(f"Rex Error: file not found: {args.file}", file=sys.stderr)
            return 1

    # support: rex file.rex
    if args.command.endswith('.rex'):
        interp = RexInterpreter()
        try:
            interp.run_file(args.command)
            return 0
        except RexError as e:
            print(f"Rex Error: {e}", file=sys.stderr)
            return 1

    parser.print_help()
    print("
Examples:")
    print("  rex run example.rex")
    print("  rex example.rex")
    return 0

if __name__ == '__main__':
    sys.exit(main())
