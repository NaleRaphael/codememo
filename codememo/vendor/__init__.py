try:
    from .settings import USE_FORKED_PYIMGUI
except ImportError as ex_use_forked_pyimgui:
    try:
        import imgui
    except ImportError:
        msg = (
            'Either original version of `pyimgui` (swistakm/pyimgui)'
            'or forked version of `pyimgui` (naleraphael/pyimgui) was '
            'installed, there is probably something wrong with the '
            'package installation.'
        )
        raise ImportError(msg) from ex_use_forked_pyimgui

    import warnings
    msg = (
        '"settings.py" are not available, fallback to use original '
        'version of `pyimgui`.'
    )
    warnings.warn(msg, UserWarning)
    USE_FORKED_PYIMGUI = False
    del warnings


import sys

if USE_FORKED_PYIMGUI:
    # ----- Load forked verion of `pyimgui` -----
    def load_pyimgui():
        from pathlib import Path
        import importlib.util

        this_dir = Path(__file__).parent
        dir_imgui = Path(this_dir, 'pyimgui', 'imgui')
        fn = Path(dir_imgui, '__init__.py')
        module_name = 'codememo.vendor.imgui'

        spec = importlib.util.spec_from_file_location('imgui', fn)
        mod = importlib.util.module_from_spec(spec)
        # Register original package name before running `exec_module()` to make
        # all submodules in it able to find their parent package (i.e. `imgui`).
        # Otherwise, we will got the following error:
        #     `ModuleNotFoundError: No module named 'imgui'`
        sys.modules['imgui'] = mod
        spec.loader.exec_module(mod)

        # Since we are binding `imgui` to our package namespace, we have to
        # add it into `sys.modules`. See also the comment in the `else` block
        # below for the reason why we have to do this.
        sys.modules[module_name] = mod

        # NOTE: We have to reload `imgui.core` in case it is the one existing in
        # installed `imgui` package in site-pacakges rather than the one in this
        # forked repository.
        if sys.platform in ('cygwin', 'win32'):
            fn_candidates = list(dir_imgui.rglob('core.*.pyd'))
        else:
            fn_candidates = list(dir_imgui.rglob('core.*.so'))

        if len(fn_candidates) > 1:
            msg = (
                'There are multiple "core.[pyd/so]" files in the forked repository, '
                'it might resulted by unclean build event before. You can try to '
                'remove them all and try again.'
            )
            raise ImportError(msg)
        elif len(fn_candidates) == 0:
            msg = (
                '"core.[pyd/so]" is not found. Forked repository `pyimgui` is '
                'probably not built sucessfully. You can try to rebuild it.'
            )
            raise ImportError(msg)

        fn = fn_candidates[0]
        spec = importlib.util.spec_from_file_location('imgui.core', fn)
        submod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(submod)
        setattr(mod, 'core', submod)

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
