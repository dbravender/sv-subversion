Users
=====

For documentation, see src/sv/__init__.py of visit http://code.google.com/p/sv-subversion/

Developers
==========

to deploy, switch into the release branch and run::

    rm setup.cfg
    python setup.py register
    python setup.py sdist bdist_egg upload -s
    svn up setup.cfg

...and don't forget to tag the release, like::
    
    sv tag release-N_N_N

maybe we can automate that one day.

You might need to update the wiki docs after a deploy too.