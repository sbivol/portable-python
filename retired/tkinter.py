import runez
from runez.pyenv import Version

from portable_python import ModuleBuilder, PPG


class Cpython(PythonBuilder):
    """Build CPython binaries"""

    def c_configure_args(self):
        # ...
        tkinter = self.active_module(TkInter)
        if tkinter:
            version = Version.from_text(tkinter.version)
            yield f"--with-tcltk-includes=-I{self.deps}/include"
            yield f"--with-tcltk-libs=-L{self.deps_lib} -ltcl{version.mm} -ltk{version.mm}"


class Tcl(ModuleBuilder):
    """
    macos: Symbol not found: _CGAffineTransformIdentity
    linux: needs X11 libs? xproto?
    """

    m_build_cwd = "unix"

    @property
    def url(self):
        return f"https://prdownloads.sourceforge.net/tcl/tcl{self.version}-src.tar.gz"

    def _prepare(self):
        for path in runez.ls_dir(self.m_src_build / "pkgs"):
            if path.name.startswith(("sqlite", "tdbc")):
                # Remove packages we don't care about and can pull in unwanted symbols
                runez.delete(path)

    def _do_linux_compile(self):
        self.run_configure("./configure", "--enable-shared=no", "--enable-threads")
        self.run_make()
        self.run_make("install")
        self.run_make("install-private-headers")


class Tk(ModuleBuilder):

    m_build_cwd = "unix"

    @property
    def url(self):
        return f"https://prdownloads.sourceforge.net/tcl/tk{self.version}-src.tar.gz"

    # noinspection PyPep8Naming
    # noinspection PyMethodMayBeStatic
    def xenv_CFLAGS(self):
        yield f"-I{self.deps}/include"

    def c_configure_args(self):
        yield "--enable-shared=no"
        yield "--enable-threads"
        yield f"--with-tcl={self.deps_lib}"
        yield "--without-x"
        if PPG.target.is_macos:
            yield "--enable-aqua=yes"

    def _do_linux_compile(self):
        self.run_configure("./configure", self.c_configure_args())
        self.run_make()
        runez.touch("wish")
        self.run_make("install")
        self.run_make("install-private-headers")


class Tix(ModuleBuilder):

    @property
    def url(self):
        return f"https://github.com/python/cpython-source-deps/archive/tix-{self.version}.tar.gz"

    @property
    def version(self):
        return self.cfg_version("8.4.3.6")

    # noinspection PyPep8Naming
    def xenv_CFLAGS(self):
        # Needed to avoid error: Getting no member named 'result' in 'struct Tcl_Interp'
        yield "-DUSE_INTERP_RESULT"
        yield "-Wno-implicit-function-declaration"  # Allows to not fail compilation due to missing 'panic' symbol
        yield f"-I{self.deps}/include"

    def c_configure_args(self):
        yield "--enable-shared=no"
        yield "--enable-threads"
        yield f"--with-tcl={self.deps_lib}"
        yield f"--with-tk={self.deps_lib}"
        yield "--without-x"

    def _do_linux_compile(self):
        self.run_configure("/bin/sh configure", self.c_configure_args())
        self.run_make()
        self.run_make("install")


class TkInter(ModuleBuilder):
    """Build tcl/tk"""

    m_debian = "tk-dev"
    m_telltale = ["{include}/tk", "{include}/tk.h"]

    @classmethod
    def candidate_modules(cls):
        return [Tcl, Tk, Tix]

    @property
    def version(self):
        return self.cfg_version("8.6.10")
