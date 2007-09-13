from setuptools import setup, find_packages
setup(
    name = "sv",
    version = "0.1",
    # if sv becomes sv/__init__.py all you need is:
    # packages = find_packages(),
    py_modules = ['sv'],
    package_dir = {'': 'src'},
    zip_safe = False,
    
    install_requires = ['lxml'],

    entry_points = { 
        'console_scripts': [ 'sv = sv:main' ] 
    },

    # metadata for upload to PyPI
    author = "Dan Bravender",
    author_email = "dan.bravender@gmail.com",
    description = "sv is a subversion wrapper that makes managing branches easier",
    license = "GPL",
    keywords = "sv subversion branching",
    url = "http://code.google.com/p/sv-subversion/wiki/HomePage",
)