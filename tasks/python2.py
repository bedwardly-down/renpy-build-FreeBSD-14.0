from renpybuild.context import Context
from renpybuild.task import task, annotator

version = "2.7.18"


@annotator
def annotate(c: Context):
    if c.python == "2":
        c.var("pythonver", "python2.7")
        c.include("{{ install }}/include/{{ pythonver }}")


@task(kind="python", pythons="2")
def unpack(c: Context):
    c.clean()

    c.var("version", version)
    c.run("tar xzf {{source}}/Python-{{version}}.tgz")


@task(kind="python", pythons="2", platforms="linux,mac,ios,freebsd")
def patch_posix(c: Context):
    c.var("version", version)

    c.chdir("Python-{{ version }}")
    c.patch("python2-no-multiarch.diff")
    c.patch("python2-cross-darwin.diff")
    c.patch("mingw-w64-python2/0001-fix-_nt_quote_args-using-subprocess-list2cmdline.patch")
    c.patch("mingw-w64-python2/0855-mingw-fix-ssl-dont-use-enum_certificates.patch")
    c.patch("python2-utf8.diff")
    c.patch("python-c-locale-utf8.diff")


@task(kind="python", pythons="2", platforms="ios")
def patch_ios(c: Context):
    c.var("version", version)

    c.chdir("Python-{{ version }}")
    c.patch("ios-python2/posixmodule.patch")

    c.run("cp {{patches}}/ios-python2/_scproxy.pyx Modules")
    c.chdir("Modules")
    c.run("cython _scproxy.pyx")


@task(kind="python", pythons="2", platforms="windows")
def patch_windows(c: Context):
    c.var("version", version)

    c.chdir("Python-{{ version }}")
    c.patchdir("mingw-w64-python2")
    c.patch("python2-no-dllmain.diff")
    c.patch("python2-utf8.diff")

    c.run(""" autoreconf -vfi """)


@task(kind="python", pythons="2", platforms="android")
def patch_android(c: Context):
    c.var("version", version)

    c.chdir("Python-{{ version }}")
    c.patchdir("android-python2")
    c.patch("mingw-w64-python2/0001-fix-_nt_quote_args-using-subprocess-list2cmdline.patch")
    c.patch("python2-utf8.diff")
    c.patch("mingw-w64-python2/0855-mingw-fix-ssl-dont-use-enum_certificates.patch")

    c.run(""" autoreconf -vfi """)


@task(kind="python", pythons="2", platforms="linux,mac,freebsd")
def build_posix(c: Context):
    c.var("version", version)

    c.chdir("Python-{{ version }}")

    with open(c.path("config.site"), "w") as f:
        f.write("ac_cv_file__dev_ptmx=no\n")
        f.write("ac_cv_file__dev_ptc=no\n")

    c.env("CONFIG_SITE", "config.site")

    c.env("CFLAGS", "{{ CFLAGS }} -DXML_POOR_ENTROPY=1 -DUSE_PYEXPAT_CAPI -DHAVE_EXPAT_CONFIG_H ")

    # Using separate sysroot jails instead of a full cross-compiler for this, so had to adjust these to get compilation to complete
    if c.platform == "freebsd":
        c.env("MACHDEP", "freebsd")
        c.env("_PYTHON_SYSCONFIGDATA_NAME", "-freebsd14")
        c.var("cross_config", "")

    c.run("""{{configure}} {{ cross_config }} --prefix="{{ install }}" --with-system-ffi --enable-ipv6""")

    c.generate("{{ source }}/Python-{{ version }}-Setup.local", "Modules/Setup.local")

    c.run("""{{ make }}""")
    c.run("""{{ make_exec }} install""")

    c.copy("{{ host }}/bin/python2", "{{ install }}/bin/hostpython2")


@task(kind="python", pythons="2", platforms="ios")
def build_ios(c: Context):
    c.var("version", version)

    c.chdir("Python-{{ version }}")

    with open(c.path("config.site"), "w") as f:
        f.write("ac_cv_file__dev_ptmx=no\n")
        f.write("ac_cv_file__dev_ptc=no\n")
        f.write("ac_cv_little_endian_double=yes\n")
        f.write("ac_cv_header_langinfo_h=no\n")
        f.write("ac_cv_func_getentropy=no\n")
        f.write("ac_cv_have_long_long_format=yes\n")

    c.env("CONFIG_SITE", "config.site")

    c.env("CFLAGS", "{{ CFLAGS }} -DXML_POOR_ENTROPY=1 -DUSE_PYEXPAT_CAPI -DHAVE_EXPAT_CONFIG_H ")

    c.run("""{{configure}} {{ cross_config }} --prefix="{{ install }}" --with-system-ffi --disable-toolbox-glue --enable-ipv6""")

    c.generate("{{ source }}/Python-{{ version }}-Setup.local", "Modules/Setup.local")

    c.run("""{{ make }} """)
    c.run("""{{ make_exec }} install""")

    c.copy("{{ host }}/bin/python2", "{{ install }}/bin/hostpython2")


@task(kind="python", pythons="2", platforms="android")
def build_android(c: Context):
    c.var("version", version)

    c.chdir("Python-{{ version }}")

    with open(c.path("config.site"), "w") as f:
        f.write("ac_cv_file__dev_ptmx=no\n")
        f.write("ac_cv_file__dev_ptc=no\n")
        f.write("ac_cv_little_endian_double=yes\n")
        f.write("ac_cv_header_langinfo_h=no\n")

    c.env("CONFIG_SITE", "config.site")

    c.env("CFLAGS", "{{ CFLAGS }} -DXML_POOR_ENTROPY=1 -DUSE_PYEXPAT_CAPI -DHAVE_EXPAT_CONFIG_H ")

    c.run("""{{configure}} {{ cross_config }} --prefix="{{ install }}" --with-system-ffi --enable-ipv6""")

    c.generate("{{ source }}/Python-{{ version }}-Setup.local", "Modules/Setup.local")

    c.run("""{{ make }}""")
    c.run("""{{ make_exec }} install""")

    c.copy("{{ host }}/bin/python2", "{{ install }}/bin/hostpython2")


@task(kind="python", pythons="2", platforms="windows")
def build_windows(c: Context):

    c.var("version", version)

    c.chdir("Python-{{ version }}")

    c.env("MSYSTEM", "MINGW")
    c.env("PYTHON_FOR_BUILD", "{{ host }}/bin/python2")

    with open(c.path("config.site"), "w") as f:
        f.write("ac_cv_func_mktime=yes")

    c.env("CFLAGS", "{{ CFLAGS }} -Wno-implicit-function-declaration -Wno-ignored-attributes -Wno-int-conversion")

    # Force a recompile.
    with open(c.path("Modules/timemodule.c"), "a") as f:
        f.write("/* MKTIME FIX */\n")

    c.env("CONFIG_SITE", "config.site")

    c.run("""{{configure}} {{ cross_config }} --enable-shared --prefix="{{ install }}" --with-threads --with-system-ffi""")

    c.generate("{{ source }}/Python-{{ version }}-Setup.local", "Modules/Setup.local")

    c.generate_text("""\
#!/bin/sh
eval $PYTHON_FOR_BUILD ../../Tools/scripts/h2py.py -i "'(u_long)'" {{cross}}/llvm-mingw/generic-w64-mingw32/include/stddef.h
""", "Lib/plat-generic/regen")

    c.run("""{{ make }}""")
    c.run("""{{ make_exec }} install""")
    c.copy("{{ host }}/bin/python2", "{{ install }}/bin/hostpython2")


@task(kind="python", pythons="2")
def pip(c: Context):
    c.run("{{ install }}/bin/hostpython2 -s -m ensurepip")
    c.run("""{{ install }}/bin/hostpython2 -s -m pip install --upgrade
        future==0.18.3
        six==1.12.0
        rsa==3.4.2
        pyasn1==0.4.2
        ecdsa==0.18.0
        urllib3==1.22
        certifi
        idna==2.6
        requests==2.20.0
        pefile==2019.4.18
        typing==3.10.0.0
        """)
