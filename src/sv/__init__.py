"""
subversion wrapper to simplify the task of branching and merging

sv is a wrapper around subversion_ to simplify the task of `branching and merging`_

Specifically, it is a command line tool written in Python that treats branches and tags as first-class names/identifiers so you can operate on them directly without worrying about starting revisions, URLs, and project paths.  Here are some reasons why sv might help you work with subversion:

- sv is optimized for many developers all working on the same project in isolated work branches.
- Since sv does not rely on properties, you can start using it on an existing repository today.
- If you are familiar with `git`_'s command line interface, sv is similar

.. _subversion: http://subversion.tigris.org/
.. _branching and merging: http://svnbook.red-bean.com/en/1.1/ch04.html
.. _git: http://git.or.cz/

Install Requirements
====================

- `svn client`_
- `Python 2.4 or greater`_
- lxml_

.. _svn client: http://subversion.tigris.org/project_packages.html
.. _Python 2.4 or greater: http://www.python.org/download/
.. _lxml: http://codespeak.net/lxml/

However, the easiest way to install sv is, by no coincidence, the following command::

    easy_install sv

You will need setuptools_ installed for this to work (and you might need root access on your machine).

.. _setuptools: http://cheeseshop.python.org/pypi/setuptools/

Documentation
=============

see `CommandReference page`_

.. _CommandReference page: http://code.google.com/p/sv-subversion/wiki/CommandReference


... or type::

    sv --help

after installation.

Bugs, Feature Requests
======================

Please feel free to `submit an issue`_

.. _submit an issue: http://code.google.com/p/sv-subversion/issues/list

Project Home
============

If you're not already here, the project lives at `Google Code`_

.. _Google Code: http://code.google.com/p/sv-subversion/

"""
__version__ = '0.3'
from sv import *