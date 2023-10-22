# Promplate

```text
</Promplate/> = /prompt/ + <template>
```

**Promplate** is a prompting framework focusing on developing experience. However, it can also be a super-convenient SDK for simple LLM calls. Promplate progressively enhance your prompting workflow. And it values flexibility as well as perfect conventions. [Learn more](https://docs.promplate.dev/py)

## IDE Support 🌹

I try to make the syntax compatible with `Jinja2`.

## Future Features (or TODOs?)

- [x] (lazy) template compiling
- [x] support any evaluatable expression inside template like `{{ [ i for i in range(n) ] }}`
- [ ] create documentation
- [ ] javascript implementation
- [ ] support chains and agents
- [ ] error handling
- [ ] template rich printing
- [x] implement component syntax `{% Component kwarg1=1, kwarg2=2, **kwargs %}`
- [x] allow more corner cases for the component syntax
  - [x] `{% Component arg=" * " %}`
  - [x] `{% Component arg = " * " %}`
  - [x] `{% Component arg = await f() %}`
- [ ] if the outer context is a `defaultdict`, the context passing to component should be?
  - or maybe this should be determined by the component itself
  - because a component could be a `Node` and a `Node` can have preprocesses
- [x] support while loop and isolated variable declaration
- [x] `else` and `elif` tag
- [ ] directory based routing
- [ ] caching (and cache-controls maybe?)
- [x] implement more [loaders](https://jinja.palletsprojects.com/api/#loaders)
  - for now you can load template from local filesystem or web urls
  - but component syntax only support variables from the context
- [x] multi-file chat template
  - using components
