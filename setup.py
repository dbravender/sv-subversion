from setuptools import setup, find_packages
import compiler, os, pydoc
from compiler import visitor

package_dir = 'src'

class ModuleVisitor(object):
    def __init__(self):
        self.mod_doc = None
        self.mod_version = None
    def default(self, node):
        for child in node.getChildNodes():
            self.visit(child)
    def visitModule(self, node):
        self.mod_doc = node.doc
        self.default(node)
    def visitAssign(self, node):
        if self.mod_version:
            return
        asn = node.nodes[0]
        assert asn.name == '__version__', (
            "expected __version__ node: %s" % asn)
        self.mod_version = node.expr.value
        self.default(node)
        
def get_module_meta(modfile):
    ast = compiler.parseFile(modfile)
    modnode = ModuleVisitor()
    visitor.walk(ast, modnode)
    if modnode.mod_doc is None:
        raise RuntimeError(
            "could not parse doc string from %s" % modfile)
    if modnode.mod_version is None:
        raise RuntimeError(
            "could not parse __version__ from %s" % modfile)
    return (modnode.mod_version,) + pydoc.splitdoc(modnode.mod_doc)

version, description, long_description = get_module_meta(
                                            os.path.join(package_dir, 'sv', '__init__.py'))

setup(
    name = "sv",
    version = version,
    packages = find_packages(package_dir),
    package_dir = {'': package_dir},
    zip_safe = False,
    
    install_requires = ['lxml'],

    entry_points = { 
        'console_scripts': [ 'sv = sv:main' ] 
    },

    # metadata for upload to PyPI
    author = "Luke Opperman, Dan Bravender, Kumar McMillan",
    author_email = "loppear@gmail.com",
    description = description,
    long_description = long_description,
    license = "GPL",
    keywords = "sv subversion branching merging",
    url = "http://code.google.com/p/sv-subversion/",
)
