# Language specification

This page is the normative description of Rex 1.0: grammar first, then the rules
the grammar cannot express.

## Notation

EBNF, as used by the Python reference manual.

```
program     ::= { statement NEWLINE }
statement   ::= let | assign | if | while | for | func
              | return | break | continue | try | throw
              | import | pass | expression
```

Newlines inside brackets, after a binary operator or after a comma are treated as
continuations and do not terminate a statement.

## Statements

```
let         ::= "rex" "." "let" NAME "=" expression
assign      ::= target "=" expression
target      ::= NAME | postfix "." NAME | postfix "[" expression "]"

if          ::= "rex" "." "if" expression block
                { "rex" "." "elif" expression block }
                [ "rex" "." "else" block ]
                "rex" "." "end"
while       ::= "rex" "." "while" expression block "rex" "." "end"
for         ::= "rex" "." "for" NAME "in" expression block "rex" "." "end"
func        ::= "rex" "." "func" NAME "(" [ params ] ")" block "rex" "." "end"
params      ::= param { "," param }
param       ::= NAME [ "=" expression ]

return      ::= "rex" "." "return" [ expression ]
break       ::= "rex" "." "break"
continue    ::= "rex" "." "continue"
pass        ::= "rex" "." "pass"

try         ::= "rex" "." "try" block
                "rex" "." "catch" NAME block
                "rex" "." "end"
throw       ::= "rex" "." "throw" expression
import      ::= "rex" "." "import" expression

block       ::= { statement NEWLINE }
```

`rex.end`, `rex.elif`, `rex.else` and `rex.catch` are reserved as block
terminators and cannot appear outside a block.

## Expressions

```
expression  ::= or
or          ::= and { ( "or" | "||" ) and }
and         ::= not { ( "and" | "&&" ) not }
not         ::= ( "not" | "!" ) not | comparison
comparison  ::= sum { ( "==" | "!=" | "<" | "<=" | ">" | ">=" ) sum }
sum         ::= product { ( "+" | "-" ) product }
product     ::= unary { ( "*" | "/" | "%" ) unary }
unary       ::= ( "-" | "+" ) unary | postfix
postfix     ::= primary { call | index | member }
call        ::= "(" [ arguments ] ")"
arguments   ::= expression { "," expression } [ "," ]
index       ::= "[" expression "]"
member      ::= "." NAME
primary     ::= NUMBER | STRING | "true" | "false" | "null"
              | NAME | list | dict | "(" expression ")"
list        ::= "[" [ expression { "," expression } [ "," ] ] "]"
dict        ::= "{" [ pair { "," pair } [ "," ] ] "}"
pair        ::= ( NAME | STRING | expression ) ":" expression
```

## Lexical rules

```
comment     ::= "#" { any character except newline }
NUMBER      ::= digit { digit | "_" } [ "." digit { digit | "_" } ]
              [ ( "e" | "E" ) [ "+" | "-" ] digit { digit } ]
STRING      ::= '"' { character | escape | interpolation } '"'
              | "'" { character | escape } "'"
interpolation ::= "${" expression "}"
NAME        ::= ( letter | "_" ) { letter | digit | "_" }
```

Escape sequences: `\n`, `\t`, `\r`, `\0`, `\b`, `\f`, `\\`, `\"`, `\'`, `\/`,
`\uXXXX`.

Strings cannot span lines; use `\n`.

## Semantics

### Scopes

1. A program runs in the global scope.
2. `rex.if`, `rex.elif`, `rex.else`, `rex.while`, `rex.for` and `rex.try` bodies
   execute in a fresh child scope of the enclosing scope.
3. Each `rex.for` iteration gets its own child scope.
4. A function body executes in a child scope of the function's definition scope
   (lexical closure).
5. `rex.let` declares in the current scope and shadows outer names.
6. Assignment updates the nearest existing declaration, or fails if there is
   none.

### Values and types

Eight types: number, string, boolean, null, list, dict, function, builtin. Numbers
are a single type; integers and floats are not distinguished by the language.

### Truthiness

`null`, `false`, `0`, `0.0`, `""`, `[]` and `{}` are false. Everything else is
true.

### Operators

| Operator | Operand types | Result |
|---|---|---|
| `+` | number, number | number |
| `+` | string, string | string |
| `+` | list, list | list |
| `-` `*` `/` `%` | number, number | number (`/` is always float) |
| `*` | string, number | string repetition |
| `*` | list, number | list repetition |
| `<` `<=` `>` `>=` | number, number | boolean |
| `<` `<=` `>` `>=` | string, string | boolean |
| `==` `!=` | any | boolean, structural and type aware |
| `and` `or` | any | one of the operands, short-circuiting |
| `not` | any | boolean |

Any other operand combination is a runtime error.

### Evaluation order

Left to right. `and` returns its left operand when falsy and otherwise evaluates
and returns the right; `or` returns its left operand when truthy and otherwise
evaluates and returns the right.

### Errors

There is one error category. Errors carry `message`, optional `hint` and optional
position (`filename`, `line`, `col`, `length`). `rex.try` catches errors raised
inside its body; it does not intercept `rex.return`, `rex.break`,
`rex.continue` or `rex.exit`.

### Execution limits

An implementation must abort after a configurable number of executed statements
(default 5,000,000) and at a configurable call depth (default 200), reporting a
normal Rex error.

### Imports

`rex.import expr` evaluates `expr` to a path, resolves relative paths against the
importing file's directory and then the working directory, and executes the file
in the current scope. Re-entering a file already on the import stack is an error.

## Reserved names

`rex` is reserved. `true`, `false`, `null`, `and`, `or`, `not` and `in` are
keywords. Everything else is a normal identifier.

## Compatibility

Within the 1.x series, the grammar above, the eight types, the operator table and
the documented builtins are stable. New builtins and new statements may be added;
existing ones will not change meaning without a major version bump.
