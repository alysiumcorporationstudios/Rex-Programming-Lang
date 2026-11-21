# env_args.rex — environment variables and command line arguments
# try: rex run examples/env_args.rex one two three
rex.show("script arguments:", rex.args)
rex.show("argument count:", rex.len(rex.args))

rex.for arg in rex.args
  rex.show("arg:", arg)
rex.end

rex.let home = rex.env("HOME", "unknown")
rex.show("HOME:", home)
rex.show("missing var fallback:", rex.env("REX_DOES_NOT_EXIST", "default value"))
