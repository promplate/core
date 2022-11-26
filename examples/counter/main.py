from src.template import Template

template = Template.load_template("index.html")

print(template.code)

with open("output.html", "w") as f:
    f.write(template.render({"nums": [1, 2, 3]}))
