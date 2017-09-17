from setuptools import setup


setup(
    name='sphinx-argparse',
    version='0.0.1',
    packages=[
        'mpy-dev-tools',
    ],
    url='https://github.com/stefanhoelzl/mpy-dev-tools',
    license='MIT',
    author='Stefan Hoelzl',
    description='development tools for micropython boards',
    long_description='Tools to mount the device as fuse-filesystem, '
                     'synchronize the file-system with your source folder and'
                     'run scripts remotly on the device.',
    install_requires=[
        'fusepy>=2.0.4',
        'pyserial>=3.4',
        'Sphinx>=1.6.3',
        'sphinx-argparse>=0.2.1',
        'sphinx_rtd_theme>=0.2.4',
        'CommonMark>=0.5.6',
    ],
)
