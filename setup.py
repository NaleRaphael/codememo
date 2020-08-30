from setuptools import setup

MAJOR = 0
MINOR = 1
MICRO = 0
VERSION = '{}.{}.{}'.format(MAJOR, MINOR, MICRO)


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
    setup_package()
