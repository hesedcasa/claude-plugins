import json


class JsonC(json.JSONDecoder):
    def __init__(self, **kw):
        super().__init__(**kw)

    def decode(self, s, _w=None):
        # Simplified comment stripper: remove '//' comments outside of quoted strings
        out = []
        in_string = False
        escape = False
        i = 0
        length = len(s)
        while i < length:
            ch = s[i]
            if escape:
                out.append(ch)
                escape = False
            elif ch == "\\":
                out.append(ch)
                escape = True
            elif ch == '"':
                out.append(ch)
                in_string = not in_string
            elif not in_string and ch == "/" and i + 1 < length and s[i + 1] == "/":
                # Skip the '//' and everything until the line end
                i += 2
                while i < length and s[i] not in ("\n", "\r"):
                    i += 1
                # Leave the newline (if any) to preserve line structure
                continue
            else:
                out.append(ch)
            i += 1
        cleaned = "".join(out)
        return super().decode(cleaned)
