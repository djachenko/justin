from setuptools import setup, find_packages

setup(
    name='justin',
    version='0.1.1',
    packages=find_packages(),
    install_requires=[
        'pyvko',
        'Pillow',
        'lazy-object-proxy',
        'justin_utils',
    ],
    url='',
    license='MIT',
    author='Harry Djachenko',
    author_email='i.s.djachenko@gmail.com',
    description='',
    entry_points={
        "console_scripts": [
            "justin = justin.runner:console_run",
        ]
    }
)
