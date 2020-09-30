"""
Currently, it's recommended to install this package with forked version
of `pyimgui` in order to enable text indentation for `input_text_multiline`
widget. You can use the following command to install:
```bash
$ pip install -v --global-option="--use-forked-pyimgui" ./
```
"""
import os, shlex, sys, site
import subprocess as sp
from pathlib import Path
from setuptools import setup, find_packages


THIS_DIR = Path(__file__).parent


def get_version(fn_version_setting):
    version = open(fn_version_setting, 'r').read().strip()
    parts = version.split('.')
    if len(parts) != 3 and not all(map(str.isnumeric, parts)):
        raise RuntimeError('Version string does not follow the standard of semantic versioning 2.0.')
    return version


def write_version_py(fn, version):
    with open(fn, 'w') as f:
        f.write(f'__version__ = "{version}"\n')


def build_forked_pyimgui():
    cmd = 'git submodule update --recursive --depth 1 --init codememo/vendor/pyimgui/'
    sp.check_call(shlex.split(cmd), cwd=THIS_DIR)

    # Preinstall Cython to build pyimgui
    cmd = 'pip install Cython>=0.29.21'
    sp.check_call(shlex.split(cmd))

    # Build extension
    dir_pyimgui = Path(THIS_DIR, 'codememo', 'vendor', 'pyimgui')
    cmd = "python setup.py build_ext --inplace"
    sp.check_call(shlex.split(cmd), cwd=dir_pyimgui)


def write_vendor_settings(use_forked_pyimgui):
    # Save variable 'USE_FORKED_IMGUI' to a file
    dir_vendor = Path(THIS_DIR, 'codememo', 'vendor')
    fn_varialbe = dir_vendor.joinpath('settings.py')

    with open(fn_varialbe, 'w') as f:
        f.write(f'USE_FORKED_PYIMGUI = {use_forked_pyimgui}')


def write_requirements():
    reqs = []
    req_imgui = 'imgui[pyglet]>=1.2.0'

    with open('./requirements.txt', 'r') as f:
        reqs = f.read().splitlines()
        if req_imgui not in reqs:
            reqs.append(req_imgui)

    with open('./requirements.txt', 'w') as f:
        f.writelines(reqs)


def get_requirements():
    with open('./requirements.txt', 'r') as f:
        reqs = f.readlines()
    return reqs


def prepare_data_files():
    path_pyimgui = ('codememo', 'vendor', 'pyimgui', 'imgui')

    files = []
    dir_pyimgui_src = Path(THIS_DIR, *path_pyimgui)
    files.extend(list(dir_pyimgui_src.rglob('*.py')))
    files.extend(list(dir_pyimgui_src.rglob('*.pyd')))
    files.extend(list(dir_pyimgui_src.rglob('*.so')))

    dir_base = Path(*path_pyimgui)
    path_map = {str(dir_base): []}

    for f in files:
        rel_path = f.relative_to(THIS_DIR)
        parent = str(rel_path.parent)
        if parent == Path('.'):
            path_map[str(dir_base)].append(f)
        else:
            rel_parent = str(parent)
            if rel_parent not in path_map:
                path_map[rel_parent] = []
            path_map[rel_parent].append(f)

    # Prefix keys in `path_map` with "lib/site-packages" (depends on OS)
    prefix = Path(site.getsitepackages()[0]).relative_to(sys.prefix)
    path_map = {str(prefix.joinpath(k)): v for k, v in path_map.items()}

    # Convert `Path` object to str
    for k in path_map:
        values = path_map[k]
        path_map[k] = [str(v) for v in values]

    data_files = list(path_map.items())
    return data_files


def setup_package():
    excluded = []
    package_data = {}

    desc = "A tool to help you trace code."

    if '--use-forked-pyimgui' in sys.argv:
        sys.argv.remove('--use-forked-pyimgui')
        build_forked_pyimgui()
        write_vendor_settings(True)
        data_files = prepare_data_files()
    else:
        write_requirements()
        write_vendor_settings(False)
        data_files = []

    version = get_version('./version.txt')
    write_version_py('./codememo/version.py', version)

    metadata = dict(
        name='codememo',
        version=version,
        description=desc,
        author='Nale Raphael',
        author_email='gmccntwxy@gmail.com',
        url='https://github.com/naleraphael/codememo',
        packages=find_packages(exclude=excluded),
        package_dir={'codememo': 'codememo'},
        data_files=data_files,
        install_requires=get_requirements(),
        classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: MIT License',
        ],
        python_requires='>=3.6',
        license='MIT',
    )

    setup(**metadata)


if __name__ == '__main__':
    setup_package()
