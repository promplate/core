# Promplate

> _Promplate_ is for **promp**t + tem**plate**

I want to build a cross-language prompt engineering framework.

## IDE Support 🌹

I try to make the syntax compatible with `Jinja2`.

## Future Features (or TODOs?)

- [ ] support spaces inside expression like `{{ a + b }}`
- [x] implement `import` syntax
- [x] support [`slot` syntax](https://svelte.dev/docs#template-syntax-slot)
  - using a component without inputting slot is just like `{% Component ~ %}`
- [ ] components with parameters
  - maybe like `{% Component arg1 arg2 kwarg1=1 kwarg2=2 %}`
- [ ] support something like [`named slot` syntax](https://svelte.dev/docs#template-syntax-slot-slot-name-name)
  - or maybe not _named_ slot, it can be a special **nullable parameter**
  - a slot may be like `{% slot ~ Name %}` and it will generate `name = context.get("name")`
  - the used component only renders once, after the end tag (a buffer seems to be unavoidable)
  - an _elevation_ of slot statements may be the necessary and sufficient condition
- [ ] support while loop and isolated variable declaration
- [ ] `else` and `elif` tag
- [x] lazy compiling(assembling)
- [ ] directory based routing
- [ ] auto refresh when template file changes detected (only in dev mode and template is valid)
- [ ] caching (and cache-controls maybe?)
- [ ] implement more [loaders](https://jinja.palletsprojects.com/api/#loaders), and complete test cases of components' grammar
