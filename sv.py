#!/usr/bin/env python
from lxml import etree
from StringIO import StringIO
from commands import getstatusoutput
from pprint import pprint
import sys, os
from optparse import OptionParser

commands = {}

def command(func):
    global commands
    commands[func.__name__] = func.__doc__
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper 

def requires_clean_working_copy(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        if len(self.changed_files) and not self.ignore_modifications:
            raise ModificationExcepion, 'Working copy has local modifications:\n   %s\nCommit, revert or ignore (-i) the changes' % '\n   '.join(self.changed_files)
        return func(*args, **kwargs)
    return wrapper

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

class Branch(object):
    multiple_project_layout = dict(
        project = lambda path: path.split('/')[0],
        branch = lambda path: path.split('/')[-1],
        trunk_path = lambda branch: '%s/trunk' % branch.project,
        branches_base_path = lambda branch: '%s/branches' % branch.project,
        tags_base_path = lambda branch: '%s/tags' % branch.project
    )
    
    one_project_layout = dict(
        project = lambda path: path.split('/')[0],
        branch = lambda path: path.split('/')[-1],
        trunk_path = lambda branch: 'trunk',
        branches_base_path = lambda branch: 'branches',
        tags_base_path = lambda branch: 'tags'
    )
    
    def __init__(self, repository_layout=None, verbose=False, execute=None, svn_info=None, ignore_modifications=False):
        if execute:
            self.execute = execute
        self.verbose = verbose
        if svn_info:
            self._svn_info = svn_info
        
        self.ignore_modifications = ignore_modifications
        self.root = self.svn_info.xpath('//root')[0].text
        self.url = self.svn_info.xpath('//url')[0].text
        self.revision = int(self.svn_info.xpath('//entry/@revision')[0])
        self.path = self.url[len(self.root) + 1:]
        
        if self.path.split('/')[0] in ['trunk', 'branches', 'tags']:
            self.repository_layout = self.one_project_layout
        else:
            self.repository_layout = self.multiple_project_layout
        
        try:
            sys.path.append(os.path.join(os.environ.get('HOME'), '.svconf'))
            self.repository_layout = full_import('svconf').repositories[self.root]
        except:
            pass
        
        self.project = self.repository_layout['project'](self.path)
        self.branch = self.repository_layout['branch'](self.path)
        self.trunk_url = '%s/%s' % (self.root, self.repository_layout['trunk_path'](self))
        self.branches_base_url = '%s/%s' % (self.root, self.repository_layout['branches_base_path'](self))
        self.tags_base_url = '%s/%s' % (self.root, self.repository_layout['tags_base_path'](self))
        
        self.message('current branch: %s (%s)' % (self.branch, self.url))
        try:
            self.branch_without_counter, self.mergeforward_counter = self.branch.split('.')
        except:
            self.branch_without_counter = self.branch
            self.mergeforward_counter = 0
        
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
            return self._branches
        branches = etree.parse(StringIO(self.execute(['svn', 'ls', '--xml', self.branches_base_url])))
        return branches.xpath('//name/text()')
    
    @command
    def tags(self):
        '''list tags'''
        # only used for testing... we don't want to cache branches (since they change when new ones are created)
        if hasattr(self, '_tags'):
            return self._tags
        branches = etree.parse(StringIO(self.execute(['svn', 'ls', '--xml', self.tags_base_url])))
        return branches.xpath('//name/text()')
    
    @property
    def changed_files(self):
        return self.svn_status.xpath('//entry/@path')
    
    @property
    def parent_url(self):
        parent_branch_path = self.svn_log.xpath('//path/@copyfrom-path')[-1]
        parent_branch_name = self.repository_layout['branch'](parent_branch_path)
        return self.latest_mergeforward_url(parent_branch_name.split('.')[0])
    
    def execute(self, command, verbose=False):
        self.message(' '.join(command))
        status, output = getstatusoutput(' '.join(command))
        if status > 0:
            raise SVException, 'Failed: %s\n>> %s' % (' '.join(command), '\n>> '.join(output.split('\n')))
        if self.verbose or verbose:
            print output
        return output
        
    def message(self, output):
        print >>sys.stderr, 'sv: %s' % output
        
    def latest_mergeforward_url(self, branch_name):
        if branch_name == 'trunk':
            return self.trunk_url
        
        branches = [branch for branch in self.branches() if branch.split('.')[0] == branch_name]
            
        def sort_merge_forwards(a, b):
            try:
                a_version = int(a.split('.')[-1])
            except:
                a_version = 0
            try:
                b_version = int(b.split('.')[-1])
            except:
                b_version = 0
            return cmp(b_version, a_version)

        branches.sort(sort_merge_forwards)
        branch_name = branches[0]
        return '%s/%s' % (self.branches_base_url, branch_name)
    
    @command
    def log(self):
        '''display svn log --stop-on-copy'''
        self.execute(['svn', 'log', '-v', '--stop-on-copy'], verbose=True)
    
    @command
    def info(self):
        '''display svn info and sv's assumptions about the repository layout'''
        self.execute(['svn', 'info'], verbose=True)
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
        '''[tag] display a diff of this branch against an arbitrary tag'''
        self.execute(['svn', 'diff', '%s/%s' % (self.tag_base_url, tag), '%s@HEAD' % self.url], verbose=True)
    
    @command
    def create(self, branch_name, parent=None):
        '''[branch_name] create a branch'''
        if self.branch == 'trunk':
            parent_url = self.trunk_url
        elif parent == None:
            parent_url = self.parent_url
        else:
            parent_url = self.latest_mergeforward_url(parent)
            
        self.execute(['svn', 'cp', parent_url, '%s/%s' % (self.branches_base_url, branch_name), '-m', '"creating branch %s"' % branch_name])
    
    @requires_clean_working_copy
    @command
    def switch(self, branch_name):
        '''[branch_name] switch to latest merge forward for a branch'''
        path = self.latest_mergeforward_url(branch_name)
        
        self.execute(['svn', 'switch', path], verbose=True)
        self.revert()
    
    @requires_clean_working_copy
    @command
    def switchtag(self, tag_name):
        '''[tag_name] switch to a tag'''
        
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
        '''tag the current branch'''
        tag_url = '%s/%s' % (self.tags_base_url, tag_name)
        
        try:
            self.execute(['svn', 'rm', tag_url, '-m', "'removing old tag'"])
        except:
            pass
        
        self.execute(['svn', 'cp', self.url, tag_url, '-m', "'creating tag %s from %s'" % (tag_url, self.url)])
    
    @requires_clean_working_copy
    @command
    def rebase(self, parent=None):
        '''[branch=trunk] merge the current branch into a new copy of the specified branch or the previous parent of the branch'''
        mergeforward_branch = '%s.%s' % (self.branch_without_counter, self.mergeforward_counter + 1)
        self.create(mergeforward_branch, parent=parent)
        start_revision = self.start_revision
        self.switch(self.branch_without_counter) # always picks up the latest
        self.merge(self.branch, start_revision, 'HEAD')
    
    @requires_clean_working_copy
    @command
    def mergeback(self, parent='trunk'):
        '''merge the current branch back into trunk'''
        if self.branch == 'trunk':
            raise MergeException, 'Merging trunk to trunk makes no sense'
        start_revision = self.start_revision
        self.switch(parent)
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
    
    @command
    def diff_files(self, before_path, before_revision, after_path, after_revision):
        return self.ls_diff(self.ls(before_path, before_revision), self.ls(after_path, after_revision))
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--ignore-modifications", dest="ignore_modifications", action="store_true",
                      help="perform actions even when modifications are present in the working copy", default=False)

    (options, args) = parser.parse_args()
    if not len(args):
        for command, help in sorted(commands.iteritems()):
            print command.rjust(15), '-', help
        parser.print_help()
    elif args[0] == 'setup':
        print 'export PATH="%s:$PATH"' % os.path.dirname(os.path.abspath(__file__))
    else:
        branch = Branch(ignore_modifications=options.ignore_modifications)
        try:
            if args[0] not in commands:
                branch.verbose = True
                branch.execute(['svn'] + args[0:])
            else:
                result = getattr(branch, args[0])(*args[1:])
                if result: 
                    pprint(result)
        except SVException, e:
            print 'Error:', str(e)
