import json
import pprint
import re
import io
import sys

# The file that the generated code will be written to.
out = None # type: io.TextIOBase

def p(s):
    """
    Writes `s` to the output file, and to stdout for debugging purposes.
    """

    out.write(s + "\n")
    sys.stdout.write(s + "\n")

# A mapping from a type to the corresponding ctypes constructor.
MAPPINGS = {
    "char" : "c_byte",
    "unsigned char" : "c_ubyte",
    "signed char" : "c_byte",
    "short" : "c_short",
    "signed_short" : "c_short",
    "unsigned short" : "c_ushort",
    "int" : "c_int",
    "signed int" : "c_int",
    "unsigned int" : "c_uint",
    "long" : "c_long",
    "signed long" : "c_long",
    "unsigned long" : "c_ulong",
    "long long" : "c_longlong",
    "signed long long" : "c_longlong",
    "unsigned long long" : "c_ulonglong",
    "char *" : "c_char_p",
    "void *" : "c_void_p",
}

class UnmappableType(Exception):
    """
    An exception that will be raised if map_type can't map the type.
    """

def map_type(name):
    """
    Given a type name, name, maps it to a ctypes type object.
    """

    rv = MAPPINGS.get(name, None)
    if rv is not None:
        return rv

    if name.startswith("const "):
        rv = map_type(name[6:])

    elif name.endswith(" *"):
        mapped = map_type(name[:-2])
        rv = f"POINTER({mapped})"

    elif name.endswith("]"):
        m = re.match(r"(.*) \[(\d+)\]", name)
        if m is None:
            raise Exception(f"Couldn't map type {name}")

        mapped = map_type(m.group(1))
        count = m.group(2)

        rv = f"({mapped} * {count})"

    elif "(*)" in name:
        raise UnmappableType(f"Couldn't map type {name}")

    else:
        raise Exception(f"Couldn't map type {name}")

    print(f"Mapped {name} to {rv}.")

    MAPPINGS[name] = rv
    return rv



def typedef(typedefs):
    """
    Processes the typedef object in steam_api.json.
    """


    for d in typedefs:

        try:

            type = map_type(d["type"])
            typedef = d["typedef"]

            print(f"Mapped {typedef} to {type}.")

            MAPPINGS[typedef] = type

        except UnmappableType:
            print(f"Skipping typedef {d}")
            continue


def consts(consts):
    """
    Processes the constants object in steam_api.json.
    """

    namespace = { }

    for c in consts:
        constname = c["constname"]
        consttype = c["consttype"]
        constval = c["constval"]

        # Correct various values that won't evaluate in python.
        if constval == "( SteamItemInstanceID_t ) ~ 0":
            constval = "-1"
        elif constval == "( ( uint32 ) 'd' << 16U ) | ( ( uint32 ) 'e' << 8U ) | ( uint32 ) 'v'":
            constval = "6579574"
        else:
            constval = re.sub(r"(0x[0-9a-fA-F]*)ull", r"\1", constval)

        # Evaluate the result, and place it into the namespace.
        value = eval(constval, namespace, namespace)
        namespace[constname] = value

        # Generate.
        mapped = map_type(consttype)

        if value > 0:
            p(f"{constname} = {mapped}(0x{value:x})")
        else:
            p(f"{constname} = {mapped}({value})")

def enums(enums):

    p("")
    p("")

    p("# Enums")

    for e in enums:
        enumname = e["enumname"]
        values = e["values"]

        p("")
        p(f"class {enumname}(c_int):")
        p("    pass")

        p("")

        for v in values:
            p(f"{v['name']} = {enumname}({v['value']})")

        p("")

        MAPPINGS[enumname] = enumname


HEADER = """\
from ctypes import POINTER, c_byte, c_ubyte, c_short, c_ushort, c_int, c_uint, c_long, c_ulong, c_longlong, c_ulonglong, c_char_p, c_void_p
"""

def main():
    with open("sdk/public/steam/steam_api.json", "r") as f:
        api = json.load(f)

    global out
    out = open("flatsteam.py", "w")

    p(HEADER)
    p("")

    typedef(api["typedefs"])

    p("# Constants")

    consts(api["consts"])


    enums(api["enums"])

    out.close()


if __name__ == "__main__":
    main()