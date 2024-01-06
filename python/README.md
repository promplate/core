# Promplate

```text
</Promplate/> = /prompt/ + <template>
```

**Promplate** is a prompting framework focusing on developing experience. However, it can also be a super-convenient SDK for simple LLM calls. Promplate progressively enhance your prompting workflow. And it values flexibility as well as perfect conventions. [Learn more](https://docs.promplate.dev/py)

## Installation

```shell
pip install promplate
```

**Promplate** supports both CPython and PyPy, from `3.8` to `3.12`.

## IDE Support 🌹

**Promplate** is fully typed, which means static type checker will find bugs correctly (if you use `pyright` for type checking).

We recommend using VS Code as your IDE when coding with promplate, because it natively uses pyright.

The language design of promplate is similar to `Jinja2`. So you can use the `.j2` file extension for template files for syntax highlight.

## Development

- use `poetry` to manage dependencies.
- use `isort` to sort import statements.
- use `black` to format code.
- use `pyright` to check type annotations.

Development should be done on `dev` branch, using `>=3.10` language features. The `master` branch is used for `py3.8` compatible releases.

**Promplate** is well tested with `pytest`. GitHub Actions are used to run tests and linting. And there are test results continually generated on [Vercel(py3.9)](https://promplate-core.vercel.app/) and [Netlify(py3.8)](https://promplate-core.netlify.app/). There is [a coverage report](https://promplate-python-coverage.onrender.com/) too.

## Future Features (or TODOs?)

- [ ] more documentation
- [ ] javascript implementation
- [ ] improve error handling
  - possible ways would be similar to [`Jinja2`](https://github.com/pallets/jinja/blob/main/src/jinja2/debug.py)
