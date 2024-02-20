# Contributing Guide

## Docker image file

### Docker Linting

We use hadolint to verify Dockerfile linting.

Please see the [documentation to install it](https://github.com/hadolint/hadolint).

```shell
> hadolint Dockerfile
Dockerfile:10 DL3008 warning: Pin versions in apt get install. Instead of `apt-get install <package>` use `apt-get install <package>=<version>`
Dockerfile:10 DL3009 info: Delete the apt-get lists after installing something
Dockerfile:22 DL3059 info: Multiple consecutive `RUN` instructions. Consider consolidation.
Dockerfile:24 DL3059 info: Multiple consecutive `RUN` instructions. Consider consolidation.
Dockerfile:68 DL3021 error: COPY with more than 2 arguments requires the last argument to end with /
```


## Python code

### Python Linting

```shell
# First install linter required using poetry
> poetry install --with=dev
# Execute ruff check
> poetry run ruff check
printer/db.py:40:13: F541 [*] f-string without any placeholders
printer/db.py:48:17: F541 [*] f-string without any placeholders
printer/db.py:68:13: F541 [*] f-string without any placeholders
printer/odoo.py:38:33: F841 [*] Local variable `e` is assigned to but never used
printer/parsers.py:6:26: F401 [*] `typing.List` imported but unused
printer/parsers.py:29:28: E711 Comparison to `None` should be `cond is None`
printer/parsers.py:38:14: E721 Do not compare types, use `isinstance()`
Found 7 errors.
[*] 5 fixable with the `--fix` option (1 hidden fix can be enabled with the `--unsafe-fixes` option).
```


You could use the option --fix if you're confortable with:

```shell
> poetry run ruff check --fix
printer/parsers.py:29:28: E711 Comparison to `None` should be `cond is None`
printer/parsers.py:38:14: E721 Do not compare types, use `isinstance()`
Found 7 errors (5 fixed, 2 remaining).
```


### Python safety-check

```shell
> poetry run safety check
+=========================================================================================================================================================+
                               /$$$$$$            /$$
                              /$$__  $$          | $$
           /$$$$$$$  /$$$$$$ | $$  \__//$$$$$$  /$$$$$$   /$$   /$$
          /$$_____/ |____  $$| $$$$   /$$__  $$|_  $$_/  | $$  | $$
         |  $$$$$$   /$$$$$$$| $$_/  | $$$$$$$$  | $$    | $$  | $$
          \____  $$ /$$__  $$| $$    | $$_____/  | $$ /$$| $$  | $$
          /$$$$$$$/|  $$$$$$$| $$    |  $$$$$$$  |  $$$$/|  $$$$$$$
         |_______/  \_______/|__/     \_______/   \___/   \____  $$
                                                          /$$  | $$
                                                         |  $$$$$$/
  by safetycli.com                                        \______/

+=========================================================================================================================================================+

 REPORT

  Safety is using PyUp's free open-source vulnerability database. This data is 30 days old and limited.
  For real-time enhanced vulnerability data, fix recommendations, severity reporting, cybersecurity support, team and project policy management
  and more sign up at https://pyup.io or email sales@pyup.io

  Safety v3.0.1 is scanning for Vulnerabilities...
  Scanning dependencies in your environment:

  -> ./Brcd-Printer
  [...]

  Using open-source vulnerability database
  Found and scanned 53 packages
  Timestamp 2024-02-20 11:09:19
  1 vulnerability reported
  0 vulnerabilities ignored

+=========================================================================================================================================================+
 VULNERABILITIES REPORTED
+=========================================================================================================================================================+

-> Vulnerability found in pillow version 9.5.0
   Vulnerability ID: 62156
   Affected spec: <10.0.0
   ADVISORY: Pillow 10.0.0 includes a fix for CVE-2023-44271: Denial of Service that uncontrollably allocates memory to process a given task,
   potentially causing a service to crash by having it run out of memory. This occurs for truetype in ImageFont when textlength in an ImageDraw
   instance operates on a long text argument.https://github.com/python-pillow/Pillow/pull/7244
   CVE-2023-44271
   For more information about this vulnerability, visit https://data.safetycli.com/v/62156/97c
   To ignore this vulnerability, use PyUp vulnerability id 62156 in safety’s ignore command-line argument or add the ignore to your safety policy file.


+=========================================================================================================================================================+
   REMEDIATIONS

  1 vulnerability was reported in 1 package. For detailed remediation & fix recommendations, upgrade to a commercial license.

+=========================================================================================================================================================+

 Scan was completed. 1 vulnerability was reported.

+=========================================================================================================================================================+

  Safety is using PyUp's free open-source vulnerability database. This data is 30 days old and limited.
  For real-time enhanced vulnerability data, fix recommendations, severity reporting, cybersecurity support, team and project policy management and more sign up at https://pyup.io or email
sales@pyup.io

+=========================================================================================================================================================+
```
