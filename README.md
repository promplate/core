# Temponent

> *Temponent* is for **temp**late + com**ponent**

I want to build a template framework in python that support component-based development like what front-end frameworks do.

## Quick Start

New an html skeleton and a component, then `render` them with some context.

<details><summary><code>main.py</code> is the html generator</summary>
<br>

```python
from src.template import Template
a = Template.load_template("index.html")
html = a.render({"nums": [1,2,3]})
print(html)
```
<br>
</details>
<details><summary><code>index.html</code> is the html skeleton</summary>
<br>

```html
{% import "counter.html" as Counter %}
<div>
    <h1> Click Me! </h1>
    {% for i in nums %}
        {% Counter %}
            {{ i }}
        {% endCounter %}
    {% endfor %}
</div>
```
<br>
</details>
<details><summary><code>button.html</code> is the component template</summary>
<br>

```html
<button onclick="arguments[0].target.innerText++">
    {% slot %}
</button>
```
<br>
</details>

Run `main.py` and you will get
```html
<div>
    <h1> Click Me! </h1>
    <button onclick="arguments[0].target.innerText++">
        1
    </button>
    <button onclick="arguments[0].target.innerText++">
        2
    </button>
    <button onclick="arguments[0].target.innerText++">
        3
    </button>
</div>
```

## IDE Support 🌹

We try to make use of IDE support for existing template engines. In fact, this is one of the major purposes of Temponent's syntax design.
Now, if you use [PyCharm](https://www.jetbrains.com/pycharm/), you can enable syntax highlight of template tokens by choosing `Jinja2` as template language [here](https://www.jetbrains.com/help/pycharm/template-languages.html#template-language-pane).

- indent inside a `slot` when reformatting the code
- navigation to a component file
- highlight of different tokens are different
- other basic IDE usages

## Future Features (or TODOs?)

- [ ] support spaces inside expression like `{{ a + b }}`
- [x] implement `import` syntax
- [x] support [`slot` syntax](https://svelte.dev/docs#template-syntax-slot)
  - using a component without inputting slot is just like `{% Component ~ %}`
- [ ] components with parameters
  -  maybe like `{% Component arg1 arg2 kwarg1=1 kwarg2=2 %}`
- [ ] support something like [`named slot` syntax](https://svelte.dev/docs#template-syntax-slot-slot-name-name)
  - or maybe not *named* slot, it can be a special **nullable parameter**
  - a slot may be like `{% slot ~ Name %}` and it will generate `name = context.get("name")`
  - the used component only renders once, after the end tag (a buffer seems to be unavoidable)
  - an *elevation* of slot statements may be the necessary and sufficient condition
- [ ] support while loop and isolated variable declaration
- [ ] `else` and `elif` tag
- [x] lazy compiling(assembling)
- [ ] directory based routing
- [ ] auto refresh when template file changes detected (only in dev mode and template is valid)
- [ ] caching (and cache-controls maybe?)
- [ ] implement more [loaders](https://jinja.palletsprojects.com/api/#loaders), and complete test cases of components' grammar
