#!/usr/bin/env python
"""sv core

see sv/__init__.py for documentation
"""

import re
from lxml import etree
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import subprocess
from pprint import pprint
import sys, os
from optparse import OptionParser
from command import command

def requires_clean_working_copy(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        if len(self.changed_files) and not self.ignore_modifications:
            raise ModificationExcepion, 'Working copy has local modifications:\n   %s\nCommit, revert or ignore (-i) the changes' % '\n   '.join(self.changed_files)
        return func(*args, **kwargs)
    return wrapper

class _SmartSort(object):
    """namespace for natural sorting functions.
    
    use smart_sort() instead of using this directly
    
    based on code from: http://code.activestate.com/recipes/285264/
    by Seo Sanghyeon and Connelly Barnes
    """
    _key_match = re.compile(r'(\d+|\D+)')
    
    def try_int(self, s):
        "Convert to integer if possible."
        try: 
            return int(s)
        except: 
            return s

    def natsort_key(self, s):
        "Used internally to get a tuple by which s is sorted."
        seq = map(self.try_int, self._key_match.findall(s))
        return seq

    def natcmp(self, a, b):
        "Natural string comparison, case sensitive."
        return cmp(self.natsort_key(a), self.natsort_key(b))
    
    def natsorted(self, seq):
        "Returns a copy of seq, sorted by natural string sort."
        seq = [s for s in seq]
        seq.sort(self.natcmp)
        return seq

def smart_sort(items):
    """sorts a list where number suffixes ending in .1 come before .12, etc"""
    s = _SmartSort()
    return s.natsorted(items)
    # return sorted(items)

class SVException(Exception):
    pass

class MergeException(SVException):
    pass
    
class ModificationExcepion(SVException):
    pass

def full_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    if hasattr(mod, components[-1]):
        mod = getattr(mod, components[-1])
    return mod

class ReposLayout(object):
    tokens = set(['trunk','branches','tags'])
    
    def __init__(self, branch):
        self.base_path = self.find_base_path(branch)
    
    def branch(self, path):
        return path.split('/')[-1]
    
    def find_base_path(self, branch):
        """given any path, returns the root path to the repository
        
        Examples::
        
            trunk/meebo/danzo.erl => "trunk"
            branches/rel_1_1/foozar/bitzor.py => "branches"
            fooz/util/tags/a-keeper/balzot.rb => "fooz/util/tags"
            
        """
        base_path = ""
        for dirname in branch.path.split('/'):
            if dirname in self.tokens:
                return base_path
            else:
                base_path = self.join_paths(base_path, dirname)
        raise SVException(
            'Could not guess repository layout (expected one of %s somewhere in path "%s")' % (
                                        ", ".join(['"%s"' % d for d in self.tokens]), branch.path))

    def join_paths(self, *paths):
        """join paths *always* with the `/' separator."""
        # don't really feel like re-writing/testing os.path.join...
        _saved_sep = os.path.sep
        os.path.sep = "/"
        try:
            return os.path.join(*paths)
        finally:
            os.path.sep = _saved_sep
    
    def trunk_path(self):
        return self.join_paths(self.base_path, 'trunk')
    
    def branches_base_path(self):
        return self.join_paths(self.base_path, 'branches')
    
    def tags_base_path(self):
        return self.join_paths(self.base_path, 'tags')
    
def get_branch_and_counter(branch):
    """returns a branch_name, counter
    
    - branch_name is the name of the branch minus any numeric counter on the end
    - the counter is the last numeric part after the dot, or 0 if one doesn't exist
    """
    dot = branch.rfind('.')
    if dot == -1:
        dot = len(branch)
    branch_name = branch[0:dot]
    last_part = branch[dot+1:]
    if last_part.isdigit():
        counter = int(last_part)
    else:
        branch_name = branch
        counter = 0
    return branch_name, counter

class Branch(object):
    def __init__(self, repository_layout=None, verbose=False, execute=None, svn_info=None, 
            ignore_modifications=False, no_switch=False, force=False):
        if execute:
            self.execute = execute
        self.verbose = verbose
        if svn_info:
            self._svn_info = svn_info
        
        self.ignore_modifications = ignore_modifications
        self.no_switch = no_switch
        self.force = force
        self.root = self.svn_info.xpath('//root')[0].text
        self.url = self.svn_info.xpath('//url')[0].text
        self.revision = int(self.svn_info.xpath('//entry/@revision')[0])
        self.path = self.url[len(self.root) + 1:]
        self.repository_layout = ReposLayout(self)
        
        self.branch = self.repository_layout.branch(self.path)
        self.trunk_url = '%s/%s' % (self.root, self.repository_layout.trunk_path())
        self.branches_base_url = '%s/%s' % (self.root, self.repository_layout.branches_base_path())
        self.tags_base_url = '%s/%s' % (self.root, self.repository_layout.tags_base_path())
        
        self.message('current branch: %s (%s)' % (self.branch, self.url))
        self.branch_without_counter, self.mergeforward_counter = get_branch_and_counter(self.branch)
        
        self.mergeforward_counter = int(self.mergeforward_counter)
        
        if self.verbose:
            self.info()
    
    @property
    def svn_info(self):
        if hasattr(self, '_svn_info'):
            return self._svn_info
        else:
            self._svn_info = etree.parse(StringIO(self.execute(['svn', 'info', '--xml'])))
            return self._svn_info
    
    @property
    def svn_log(self):
        if hasattr(self, '_svn_log'):
            return self._svn_log
        else:
            self._svn_log = etree.parse(StringIO(self.execute(['svn', 'log', '-v', '--stop-on-copy', '--xml'])))
            return self._svn_log
    
    @property
    def start_revision(self):
        return int(self.svn_log.xpath('//logentry/@revision')[-1])
    
    @property
    def head_revision(self):
        return int(self.svn_log.xpath('//logentry/@revision')[0])
    
    @property
    def svn_status(self):
        if hasattr(self, '_svn_status'):
            return self._svn_status
        else:
            self._svn_status = etree.parse(StringIO(self.execute(['svn', 'status', '--xml'])))
            return self._svn_status
    
    @command
    def branches(self):
        '''list branches'''
        # only used for testing... we don't want to cache branches (since they change when new ones are created)
        if hasattr(self, '_branches'):
            return self._branches.pop(0)
        branches = etree.parse(StringIO(self.execute(['svn', 'ls', '--xml', self.branches_base_url])))
        return branches.xpath('//name/text()')
    
    @command
    def tags(self):
        '''list tags'''
        # only used for testing... we don't want to cache branches (since they change when new ones are created)
        if hasattr(self, '_tags'):
            return self._tags
        branches = etree.parse(StringIO(self.execute(['svn', 'ls', '--xml', self.tags_base_url])))
        return smart_sort(branches.xpath('//name/text()'))
    
    @property
    def changed_files(self):
        # LDO: issue1, don't count unversioned files as changed
        return self.svn_status.xpath('//wc-status[@item!="unversioned"]/parent::entry/@path')

    @property
    def parent_url(self):
        added = []
        for path in self.svn_log.xpath('//path[@action="A"]/@copyfrom-path'):
            added.append(path)
        if len(added) == 0:
            raise ValueError(
                'unexpected log output: could not find any //path[@action="A"]/@copyfrom-path elements')
        parent_branch_path = added[-1]
        parent_branch_name = self.repository_layout.branch(parent_branch_path)
        return self.latest_mergeforward_url(parent_branch_name.split('.')[0])
    
    def execute(self, command, verbose=False):
        self.message(' '.join(command))
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        status = p.returncode
        output = (stdout or "") + (stderr or "")
        ## fixme: this would benefit greatly from streaming the output (as a file) directly to lxml.
        ## The code here was a replacement for getstatusoutput() which was causing some piping problems 
        ## while talking to the svn command (issue:17)
        if status > 0:
            raise SVException, 'Failed: %s\n>> %s' % (' '.join(command), '\n>> '.join(output.split('\n')))
        if self.verbose or verbose:
            print output
        return output
        
    def message(self, output):
        print >>sys.stderr, 'sv: %s' % output
        
    def mergeforward_branches(self, branch_name=None, do_sort=False):
        if branch_name is None:
            branch_name = self.branch
        branch_name, counter = get_branch_and_counter(branch_name)
        branches = [branch for branch in self.branches() if get_branch_and_counter(branch)[0] == branch_name]
        def get_suffix_as_int(branch):
            if branch.count('.'):
                suf = branch.split('.')[-1]
            else:
                suf = None
            if suf is not None and suf.isdigit():
                return int(suf)
            else:
                return 0
        if do_sort:
            branches.sort(key=get_suffix_as_int, reverse=True)
        return branches

    def latest_mergeforward_url(self, branch_name):
        if branch_name == 'trunk':
            return self.trunk_url
        
        branches = self.mergeforward_branches(branch_name, do_sort=True)
        if branches:
            branch_name = branches[0]
        return '%s/%s' % (self.branches_base_url, branch_name)

    def determine_parent_url(self, parent_arg):
        if self.branch == 'trunk':
            parent_url = self.trunk_url
        elif parent_arg == None:
            parent_url = self.parent_url
        else:
            parent_url = self.latest_mergeforward_url(parent_arg)
        return parent_url


    @command(aliases=['up'])
    def update(self):
        '''svn update, but switches to latest rebase if necessary'''
        branches = self.mergeforward_branches(do_sort=True)
        if [self.branch] == (branches[:1] or ['trunk']):
            self.execute(['svn', 'up'], verbose=True)
        else:
            self.switch(self.branch_without_counter)
        

    @command
    def log(self):
        '''display svn log --stop-on-copy'''
        for branch in self.mergeforward_branches(do_sort=True):
            branch_url = '%s/%s' % (self.branches_base_url, branch)
            self.execute(['svn', 'log', '-v', '--stop-on-copy', branch_url], verbose=True)
    
    @command
    def info(self):
        '''display svn info and assumptions about the repository layout'''
        self.execute(['svn', 'info'], verbose=True)
#        self.message('parent branch: %s' % self.repository_layout['branch'](self.parent_url))
        self.message('using repository layout:\n    trunk    = %s\n    branches = %s\n    tags     = %s\n' % (self.trunk_url, self.branches_base_url, self.tags_base_url))
    
    @command
    def branchdiff(self):
        '''display a diff from stop-on-copy to HEAD'''
        self.execute(['svn', 'diff', '%s@%d' % (self.url, self.start_revision), '%s@HEAD' % self.url], verbose=True)
    
    @command
    def difftotrunk(self):
        '''display a diff of this branch against trunk'''
        self.execute(['svn', 'diff', self.trunk_url, '%s@HEAD' % self.url], verbose=True)
    
    @command
    def difftotag(self, tag):
        '''<tag_name> display a diff of this branch against a tag'''
        self.execute(['svn', 'diff', '%s/%s' % (self.tag_base_url, tag), '%s@HEAD' % self.url], verbose=True)

    @requires_clean_working_copy
    @command
    def create(self, branch_name, parent=None):
        '''<branch_name> [parent=parent] create a branch based on parent'''
        if branch_name in self.branches():
            raise SVException("Cannot create branch '%s', already exists" % branch_name)
        parent_url = self.determine_parent_url(parent)
        self.execute(['svn', 'cp', parent_url, '%s/%s' % (self.branches_base_url, branch_name), '-m', '"creating branch %s"' % branch_name])
        if not self.no_switch:
            self.switch(branch_name)

    @requires_clean_working_copy
    @command
    def createtag(self, tag_name):
        '''<tag_name> create a tag from this branch'''
        if tag_name in self.tags():
            raise SVException("Cannot create tag '%s', already exists" % tag_name)
        if self.branch == 'trunk':
            copy_from_branch = self.trunk_url
        else:
            # we are in a branch, copy from the latest :
            copy_from_branch = self.latest_mergeforward_url(self.branch)
            
        self.execute(['svn', 'cp', copy_from_branch, '%s/%s' % (self.tags_base_url, tag_name), '-m', '"creating tag %s"' % tag_name])
        if not self.no_switch:
            self.switchtag(tag_name)
    
    @requires_clean_working_copy
    @command
    def switch(self, branch_name, is_url=False):
        '''<branch_name> switch to latest rebase for a branch'''
        if is_url:
            path = branch_name
        else:
            path = self.latest_mergeforward_url(branch_name)
        
        self.execute(['svn', 'switch', path], verbose=True)
        self.revert()
    
    @requires_clean_working_copy
    @command
    def switchtag(self, tag_name):
        '''<tag_name> switch to a tag'''
        
        self.execute(['svn', 'switch', '%s/%s' % (self.tags_base_url, tag_name)])
        self.revert()
    
    @command
    def revert(self):
        '''svn revert -R .'''
        if not self.ignore_modifications:
            self.execute(['svn', 'revert', '-R', '.'])
    
    def merge(self, branch_name, start_revision, end_revision):
        self.execute(['svn', 'merge', '-r%s:%s' % (start_revision, end_revision), '%s/%s' % (self.branches_base_url, branch_name)], verbose=True)
    
    @requires_clean_working_copy
    @command
    def tag(self, tag_name):
        '''<tag_name> tag this branch'''
        if self.branch == 'trunk':
            tag_from = self.trunk_url
        else:
            latest_branch = self.mergeforward_branches(self.branch, do_sort=True)[0]
            if not self.force and self.branch != latest_branch:
                raise SVException(
                    "cowardly refusing to tag current branch, %s, because a newer one "
                    "exists: %s (set --force to continue anyway)" % (
                        self.branch, latest_branch))
            tag_from = "%s/%s" % (self.branches_base_url, self.branch)
        
        tag_url = '%s/%s' % (self.tags_base_url, tag_name)
        
        if tag_name in self.tags():
            if not self.force:
                raise SVException(
                    "cannot create tag '%s', it already exists (set --force to remove "
                    "it and continue)" % tag_name)             
            self.execute(['svn', 'rm', tag_url, '-m', 
                '"removing tag %s (going to re-tag %s)"' % (tag_name, tag_from)])
        
        self.execute(['svn', 'cp', tag_from, tag_url, '-m', 
            "'creating tag %s from %s'" % (tag_url, tag_from)])
    
    @requires_clean_working_copy
    @command
    def rebase(self, parent=None):
        '''[parent=parent] merge this branch into a new copy of parent'''
        assert not self.no_switch, "--no-switch cannot be used with rebase"
        mergeforward_branch = '%s.%s' % (self.branch_without_counter, self.mergeforward_counter + 1)
        start_revision = self.start_revision
        self.create(mergeforward_branch, parent=parent)
        self.merge(self.branch, start_revision, 'HEAD')
    
    @requires_clean_working_copy
    @command
    def mergeback(self, parent=None):
        '''[destination=parent] merge this branch back into destination'''
        if self.branch == 'trunk':
            raise MergeException, 'Merging trunk to trunk makes no sense'
        start_revision = self.start_revision
        parent_url = self.determine_parent_url(parent)
        self.switch(parent_url, is_url=True)
        self.merge(self.branch, start_revision, 'HEAD')
    
    def ls_diff(self, before, after):
        before_files = dict(zip(before.xpath('//entry/name/text()'), before.xpath('//entry/commit/@revision')))
        after_files = dict(zip(after.xpath('//entry/name/text()'), after.xpath('//entry/commit/@revision')))
        
        new_files = set(after_files.keys()) - set(before_files.keys())
        old_files = set(before_files.keys()).intersection(set(after_files.keys()))
        modified_files = new_files
        for filename in old_files:
            if after_files[filename] > before_files[filename]:
                modified_files |= set([filename])
        
        return list(modified_files)
    
    def ls(self, path, revision='HEAD'):
        return etree.parse(StringIO(self.execute(['svn', 'ls', '--xml', '%s/%s@%s' % (self.root, path, revision)])))
    
    
    def diff_files(self, before_path, before_revision, after_path, after_revision):
        return self.ls_diff(self.ls(before_path, before_revision), self.ls(after_path, after_revision))
        
def main():
    usage = '\n'
    for comm, help in sorted(command.help.iteritems()):
            usage += "%s - %s\n" % (comm.rjust(15), help)
       
    parser = OptionParser(usage=usage)
    parser.add_option("-i", "--ignore-modifications", dest="ignore_modifications", action="store_true",
              help="perform actions even when modifications are present in the working copy", default=False)
    parser.add_option("--force", dest="force", action="store_true",
              help="perform an action that would otherwise generate a warning", default=False)
    parser.add_option("--no-switch", dest="no_switch", action="store_true", default=False,
                      help="for create, do not switch to the newly created branch")

    (options, args) = parser.parse_args()
    if not len(args):
        parser.print_help()
    elif args[0] == 'setup':
        print 'export PATH="%s:$PATH"' % os.path.dirname(os.path.abspath(__file__))
    else:
        branch = Branch(
            ignore_modifications=options.ignore_modifications, 
            no_switch=options.no_switch,
            force=options.force)
        try:
            if args[0] not in command.commands:
                branch.verbose = True
                branch.execute(['svn'] + args[0:])
            else:
                result = command.commands[args[0]](branch, *args[1:])
                if result: 
                    pprint(result)
        except SVException, e:
            print 'Error:', str(e)
    
if __name__ == '__main__':
    main()
