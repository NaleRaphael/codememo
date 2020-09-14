import shlex, sys
import subprocess as sp
from pathlib import Path
from setuptools import setup


this_dir = Path(__file__).parent

MAJOR = 0
MINOR = 1
MICRO = 0
VERSION = '{}.{}.{}'.format(MAJOR, MINOR, MICRO)


def build_forked_pyimgui():
    cmd = 'git submodule update --recursive --init codememo/vendor/pyimgui/'
    sp.check_call(shlex.split(cmd), cwd=this_dir)

    # Preinstall Cython to build pyimgui
    cmd = 'pip install Cython>=0.29.21'
    sp.check_call(shlex.split(cmd))

    dir_pyimgui = Path(this_dir, 'codememo', 'vendor', 'pyimgui')
    cmd = "python setup.py build_ext --inplace"
    sp.check_call(shlex.split(cmd), cwd=dir_pyimgui)


def write_vendor_settings(use_forked_pyimgui):
    # Save variable 'USE_FORKED_IMGUI' to a file
    dir_vendor = Path(this_dir, 'codememo', 'vendor')
    fn_varialbe = dir_vendor.joinpath('settings.py')

    with open(fn_varialbe, 'w') as f:
        f.write(f'USE_FORKED_PYIMGUI = {use_forked_pyimgui}')


def write_requirements():
    with open('./requirements.txt', 'a') as f:
        f.write('imgui[pyglet]>=1.2.0')


def get_requirements():
    with open('./requirements.txt', 'r') as f:
        reqs = f.readlines()
    return reqs


def setup_package():
    excluded = []
    package_data = {}

    desc = "A tool to help you trace code."

    metadata = dict(
        name='codememo',
        version=VERSION,
        description=desc,
        author='Nale Raphael',
        author_email='gmccntwxy@gmail.com',
        url='https://github.com/naleraphael/codememo',
        packages=['codememo'],
        package_dir={'codememo': 'codememo'},
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
    # NOTE: Use the following command to install this package with
    # forked pyimgui.
    # ```bash
    # $ pip install -v --global-option="--use-forked-pyimgui" ./
    # ```
    if '--use_forked_pyimgui' in sys.argv:
        sys.argv.remove('--use_forked_pyimgui')
        build_forked_pyimgui()
        write_vendor_settings(True)
    else:
        write_requirements()
        write_vendor_settings(False)

    setup_package()
