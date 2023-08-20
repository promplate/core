# Promplate

> _Promplate_ is for **promp**t + tem**plate**

I want to build a cross-language prompt engineering framework.

## IDE Support 🌹

I try to make the syntax compatible with `Jinja2`.

## Future Features (or TODOs?)

- [x] (lazy) template compiling
- [x] support any evaluatable expression inside template like `{{ [ i for i in range(n) ] }}`
- [ ] support chains and agents
- [ ] error handling
- [ ] template rich printing
- [ ] implement component syntax
  - maybe like `{% Component arg1 arg2 kwarg1=1 kwarg2=2 %}`
- [ ] support something like [`named slot` syntax](https://svelte.dev/docs#template-syntax-slot-slot-name-name)
  - or maybe not _named_ slot, it can be a special **nullable parameter**
  - a slot may be like `{% slot ~ Name %}` and it will generate `name = context.get("name")`
  - the used component only renders once, after the end tag (a buffer seems to be unavoidable)
  - an _elevation_ of slot statements may be the necessary and sufficient condition
- [ ] support while loop and isolated variable declaration
- [ ] `else` and `elif` tag
- [ ] directory based routing
- [ ] caching (and cache-controls maybe?)
- [ ] implement more [loaders](https://jinja.palletsprojects.com/api/#loaders)
- [ ] multi-file chat template
