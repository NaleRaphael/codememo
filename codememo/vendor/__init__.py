# TODO: make this configurable
USE_FORKED_IMGUI = True

import sys

if USE_FORKED_IMGUI:
    # ----- Load forked verion of `pyimgui` -----
    def load_pyimgui():
        from pathlib import Path
        import importlib.util

        this_dir = Path(__file__).parent
        fn = Path(this_dir, 'pyimgui', 'imgui', '__init__.py')
        module_name = 'codememo.vendor.imgui'

        spec = importlib.util.spec_from_file_location(module_name, fn)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Since we are binding `imgui` to our package namespace, we have to
        # add it into `sys.modules`. See also the comment in the `else` block
        # below for the reason why we have to do this.
        sys.modules[module_name] = mod
        return mod

    imgui = load_pyimgui()

else:
    # ----- Load official version of `pyimgui` -----
    import imgui

    # Add our namespace to `sys.modules`, so that we can:
    # - Import `imgui` from our package namespace, e.g.
    #   `import codememo.vendor.imgui`
    # - Import submodules from `imgui`, e.g.
    #   `from codememo.vendor.imgui import integrations`
    sys.modules['codememo.vendor.imgui'] = imgui


__all__ = ['imgui']

del sys
