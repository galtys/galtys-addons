from distutils.core import setup

setup(
    name='skynetlib',
    version='1.1',
    description='experimental module to implement HashSync Protocol',
    author='Jan Troler',
    author_email='jan.troler@galtys.com',
    url='git@github.com:galtys/galtys-addons.git',
    packages=['skynetlib'],
    install_requires=[
        'requests>=2.0.1',
        'simple-crypt>=3.0.2',
    ],
    license='MIT',
    scripts=[
#        'bin/golive'
    ],
)
