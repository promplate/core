def appender(to_append: list):
    def append_processer(func):
        to_append.append(func)

        return func

    return append_processer
