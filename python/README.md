# Promplate

```text
</Promplate/> = /prompt/ + <template>
```

**Promplate** is a prompting framework focusing on developing experience. However, it can also be a super-convenient SDK for simple LLM calls. Promplate progressively enhance your prompting workflow. And it values flexibility as well as perfect conventions. [Learn more](https://docs.promplate.dev/py)

## Installation

```shell
pip install promplate
```

## Development

- use `poetry` to manage dependencies.
- use `isort` to sort import statements.
- use `black` to format code.
- use `pyright` to check type annotations.

## IDE Support 🌹

I try to make the syntax compatible with `Jinja2`. So for now I recommend using `Jinja2` highlight settings.

## Future Features (or TODOs?)

- [ ] more documentation
- [ ] javascript implementation
- [ ] improve error handling
  - possible ways would be similar to [`Jinja2`](https://github.com/pallets/jinja/blob/main/src/jinja2/debug.py)
- [x] streaming support
- [x] unit tests
  - coverage report [here](https://promplate-python-coverage.onrender.com/)
- [x] the order of callbacks is reversed for `on_leave` and `end_process`
