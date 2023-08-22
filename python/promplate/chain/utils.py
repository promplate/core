def append_decorator(to_append: list):
    def append_item(item):
        to_append.append(item)

    return append_item
