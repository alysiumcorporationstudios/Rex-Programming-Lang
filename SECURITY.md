# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 1.x | yes |
| 0.1.x | no, please upgrade |

## Reporting a vulnerability

Please do **not** open a public issue for a security problem. Email
**alysium.corporation.studios@gmail.com** with:

- the Rex version (`rex version`),
- the smallest `.rex` program that reproduces the problem,
- what an attacker could achieve with it,
- any mitigation you have already found.

You can expect an acknowledgement within a few days and a fix or a written
assessment within 30 days. Credit is given in the release notes unless you ask
otherwise.

## Threat model

Rex is a scripting language that runs trusted code. A `.rex` file can:

- read and write files the user can access,
- make network requests,
- read environment variables,
- run until the statement budget is exhausted.

That is by design, and it is the same model as a shell script or a Python file.
Rex is **not** a sandbox. Do not run untrusted `.rex` files any more than you
would run an untrusted shell script.

## Built-in limits

- `--max-steps` (default 5,000,000 statements) bounds runaway loops.
- `--max-depth` (default 200 calls) bounds runaway recursion.
- HTTP builtins apply a default 15 second timeout.
- `rex.read`, `rex.write` and `rex.append` are limited to the permissions of the
  process that started Rex.

## In scope

- Crashes reachable from a `.rex` file (Python tracebacks instead of Rex errors).
- Path handling that lets a `.rex` file write somewhere it should not, beyond the
  user's own permissions.
- Denial of service that bypasses the step and depth limits.
- Anything that leaks a secret through output that should not contain it.

## Out of scope

- Running a `.rex` file you do not trust.
- A script deliberately reading your environment or files.
- Vulnerabilities in `requests`, Python or your operating system.
