import io
import contextlib


def execute_code(code):
    output = io.StringIO()

    try:
        with contextlib.redirect_stdout(output):
            exec(code, {"__name__": "__main__"})

        return output.getvalue()

    except Exception as e:
        return f"Runtime Error: {e}"