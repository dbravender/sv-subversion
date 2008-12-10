from sv import get_branch_and_counter, smart_sort, Branch, ReposLayout, SVException
import fixtures
import nose
from nose.tools import eq_, raises

def dont_execute(cls, command, *args, **kwargs):
    raise Exception, 'Tried to execute %s' % command

# we don't want the tests to _ever_ execute commands
Branch.execute = dont_execute

def mock_execute(expected_commands):
    def execute(command, *args, **kwargs):
        eq_( command , expected_commands[execute.count])
        execute.count += 1
        if execute.count == len(expected_commands):
            execute.finished = True
    execute.count = 0
    execute.finished = False
    return execute

class BranchTest(object):
    def setup(self):
        # svn info since is needed during init
        self.branch = Branch(svn_info=fixtures.info)

def test_get_branch_and_counter():
    eq_(get_branch_and_counter("foo"), ('foo', 0))
    eq_(get_branch_and_counter("foo.0"), ('foo', 0))
    eq_(get_branch_and_counter("foo.1"), ('foo', 1))
    eq_(get_branch_and_counter("foo.999"), ('foo', 999))
    eq_(get_branch_and_counter("foo.bazzo"), ('foo.bazzo', 0))
    eq_(get_branch_and_counter("foo.bazzo.1"), ('foo.bazzo', 1))

def test_smart_sort():
    eq_([i for i in smart_sort(['0.1.10', '0.1.9', 'foo', 'foo.17', 'foo.2'])],
        ['0.1.9', '0.1.10', 'foo', 'foo.2', 'foo.17'])

class TestBranch(BranchTest):    
    def test_info(self):
        assert self.branch.root == 'svn+ssh://dev/vol2/svn'
        assert self.branch.path == 'monkey/trunk'
        assert self.branch.revision == 18799
        assert self.branch.repository_layout.base_path == 'monkey'
        assert self.branch.branch == 'trunk'
        assert self.branch.url == 'svn+ssh://dev/vol2/svn/monkey/trunk'
        assert self.branch.trunk_url == 'svn+ssh://dev/vol2/svn/monkey/trunk'
        assert self.branch.branches_base_url == 'svn+ssh://dev/vol2/svn/monkey/branches'
        assert self.branch.tags_base_url == 'svn+ssh://dev/vol2/svn/monkey/tags'
        
    def test_revisions(self):
        self.branch._svn_log = fixtures.log
        assert self.branch.start_revision == 18496
        assert self.branch.head_revision == 18497
    
    def test_branchdiff(self):
        self.branch._svn_log = fixtures.log
        self.branch.execute = mock_execute([['svn', 'diff', 'svn+ssh://dev/vol2/svn/monkey/trunk@18496', 'svn+ssh://dev/vol2/svn/monkey/trunk@HEAD']])
        self.branch.branchdiff()
    
    def test_message(self):
        self.branch.message('test')
        
    def test_no_modifications(self):
        self.branch._svn_status = fixtures.status_clean
        assert not self.branch.changed_files
    
    def test_modifications(self):
        self.branch._svn_status = fixtures.status_changes
        assert len(self.branch.changed_files) == 1
    
    def test_revert(self):
        self.branch.execute = mock_execute([['svn', 'revert', '-R', '.']])
        self.branch.revert()

    def test_ignore_mod_revert_is_noop(self):
        branch = Branch(svn_info=fixtures.info, ignore_modifications=True)
        branch.execute = mock_execute([])
        branch.revert()

    def test_ls_diff(self):
        assert self.branch.ls_diff(fixtures.ls_before_changes, fixtures.ls_after_changes) == ['added_file', 'sv.py']        
    
    def test_merge(self): 
        self.branch.execute = mock_execute([['svn', 'merge', '-r18496:HEAD', 'svn+ssh://dev/vol2/svn/monkey/branches/some_other_branch']])
        self.branch.merge('some_other_branch', '18496', 'HEAD')
     
        self.sv = Branch(svn_info=fixtures.info_merged_forward)
        self.branch.execute = mock_execute([['svn', 'merge', '-r18496:HEAD', 'svn+ssh://dev/vol2/svn/monkey/branches/some_other_branch']])
        self.branch.merge('some_other_branch', '18496', 'HEAD')
        
    def test_create(self):
        self.branch._svn_log = fixtures.log_trunk_branch_parent
        self.branch._branches = [
            ['some_other_branch'],
            ['some_other_branch']]
        self.branch._svn_status = fixtures.status_clean
        self.branch.execute = mock_execute([
            ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/trunk', 'svn+ssh://dev/vol2/svn/monkey/branches/test_branch', '-m', '"creating branch test_branch"'],
            ['svn', 'switch', 'svn+ssh://dev/vol2/svn/monkey/branches/test_branch'],
            ['svn', 'revert', '-R', '.']
            ])
        self.branch.create('test_branch')
        assert self.branch.execute.finished

    def test_create_no_switch(self):
        branch = Branch(svn_info=fixtures.info_merged_forward, no_switch=True)
        branch._svn_log = fixtures.log_trunk_branch_parent
        branch._branches = [['some_other_branch']]
        branch._svn_status = fixtures.status_clean
        branch.execute = mock_execute([
            ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/trunk', 'svn+ssh://dev/vol2/svn/monkey/branches/test_branch', '-m', '"creating branch test_branch"']
            ])
        branch.create('test_branch')
        assert branch.execute.finished

    @nose.tools.raises(SVException)
    def test_create_fails_if_exists(self):
        branch = Branch(svn_info=fixtures.info_merged_forward)
        branch._svn_status = fixtures.status_clean
        branch._branches = [['some_branch']]
        branch.create('some_branch')

class TestBranchCreateVariations(object):

    def setup(self):
        branch = Branch(svn_info=fixtures.info_merged_forward, no_switch=True)
        branch._svn_log = fixtures.log_non_trunk_branch_parent
        branch._svn_status = fixtures.status_clean
        branch._branches = [
            ['jquery.1', 'jquery.2', 'jquery.3', 'some_other_branch', 'some_other_branch.1'],
            # simulate after copy:
            ['jquery.1', 'jquery.2', 'jquery.3', 'some_other_branch', 'some_other_branch.1', 'test_branch']]
        self.branch = branch
        
    def test_create_different_parent_no_switch(self):
        self.branch.execute = mock_execute([
            ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/branches/some_other_branch.1', 'svn+ssh://dev/vol2/svn/monkey/branches/test_branch', '-m', '"creating branch test_branch"']])
        self.branch.create('test_branch')

    def test_create_specified_parent_no_switch(self):
        self.branch.execute = mock_execute([
            ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.3', 'svn+ssh://dev/vol2/svn/monkey/branches/test_branch', '-m', '"creating branch test_branch"']])
        self.branch.create('test_branch', 'jquery')


    def test_create_with_copied_in_files(self):
        self.branch._svn_log = fixtures.log_non_trunk_branch_parent_with_copies
        self.branch.execute = mock_execute([
            ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/branches/some_other_branch.1', 'svn+ssh://dev/vol2/svn/monkey/branches/test_branch', '-m', '"creating branch test_branch"']])
        self.branch.create('test_branch')


class TestTag(object):

    @nose.tools.raises(SVException)
    def test_tag_fails_if_exists(self):
        branch = Branch(svn_info=fixtures.tag_from_trunk.info)
        branch._svn_log = fixtures.tag_from_trunk.log
        branch._svn_status = fixtures.tag_from_trunk.status
        branch._tags = ['some_tag']
        branch._branches = [[]]
        branch.tag('some_tag')
        
    def test_tag_removes_current_tag_if_exists_with_force_option(self):
        branch = Branch(svn_info=fixtures.tag_from_trunk.info, force=True)
        branch._svn_log = fixtures.tag_from_trunk.log
        branch._svn_status = fixtures.tag_from_trunk.status
        branch._tags = ['test_tag']
        branch._branches = [[]]
        branch.execute = mock_execute([
            ['svn', 'rm', 'svn+ssh://dev/vol2/svn/monkey/tags/test_tag', 
                '-m', '"removing tag test_tag (going to re-tag svn+ssh://dev/vol2/svn/monkey/trunk)"'],
            ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/trunk', 
                'svn+ssh://dev/vol2/svn/monkey/tags/test_tag', '-m', (
                    "'creating tag svn+ssh://dev/vol2/svn/monkey/tags/test_tag from "
                    "svn+ssh://dev/vol2/svn/monkey/trunk'")],
            ])
        branch.tag('test_tag')
        assert branch.execute.finished

    def test_tag_from_trunk(self):
        branch = Branch(svn_info=fixtures.tag_from_trunk.info)
        branch._svn_log = fixtures.tag_from_trunk.log
        branch._svn_status = fixtures.tag_from_trunk.status
        branch._tags = ['some_tag']
        branch.execute = mock_execute([
            ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/trunk', 
                'svn+ssh://dev/vol2/svn/monkey/tags/test_tag', '-m', (
                    "'creating tag svn+ssh://dev/vol2/svn/monkey/tags/test_tag from "
                    "svn+ssh://dev/vol2/svn/monkey/trunk'")],
            ])
        branch.tag('test_tag')
        assert branch.execute.finished
    
    @nose.tools.raises(SVException)
    def test_tag_warns_if_not_in_latest_branch(self):
        branch = Branch(svn_info=fixtures.tag_from_latest_branch.info)
        branch._svn_log = fixtures.tag_from_latest_branch.log
        branch._svn_status = fixtures.tag_from_latest_branch.status
        branch._tags = ['some_tag']
        branch._branches = [['jquery.1', 'jquery.2', 'jquery.3']]
        branch.tag('test_tag')
        
    def test_tag_current_branch_if_not_latest_with_force(self):
        branch = Branch(svn_info=fixtures.tag_from_latest_branch.info, force=True)
        branch._svn_log = fixtures.tag_from_latest_branch.log
        branch._svn_status = fixtures.tag_from_latest_branch.status
        branch._tags = ['some_tag']
        branch._branches = [['jquery.1', 'jquery.2', 'jquery.3']]
        branch.execute = mock_execute([
            # since we are in jquery.1, we want to copy from the latest :
            ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.2', 
                'svn+ssh://dev/vol2/svn/monkey/tags/test_tag', 
                '-m', (
                    "'creating tag svn+ssh://dev/vol2/svn/monkey/tags/test_tag from "
                    "svn+ssh://dev/vol2/svn/monkey/branches/jquery.2'")]
            ])
        branch.tag('test_tag')
        assert branch.execute.finished
        
    def test_tag_should_copy_from_branch_and_ignore_R_action(self):
        """test_tag_should_copy_from_branch_and_ignore_R_action
        
        The two bugs (issue:22), (issue:23):
        
        - createtag / tag does not copy from the branch you are in (if you are in one)
        - The "R" action is not ignored when the copyfrom-path attribute in the path element is analyzed. 
          See http://svn.haxx.se/users/archive-2007-10/0280.shtml , which explains the strange "R" action.  
          This is a peculiar copy-from action that I still don't fully understand.  In this case, it looks 
          like trunk was copied into branch_foo, but then a file, setup.py was modified and thus is marked 
          as "R" or Replaced.
        
        """
        branch = Branch(svn_info=fixtures.from_branch_with_R.info)
        branch._svn_status  = fixtures.from_branch_with_R.status
        branch._svn_log     = fixtures.from_branch_with_R.log
        branch._branches    = [['PR27', 'PR28']]
        branch._tags    = ['PR27.0', 'PR27.1' 'PR28.0']
        branch.execute = mock_execute(
            [
                ['svn', 'cp', 'svn+ssh://kumar@dev/vol2/svn/etl/branches/PR28', 
                    'svn+ssh://kumar@dev/vol2/svn/etl/tags/PR28.1', 
                    '-m', (
                        "'creating tag svn+ssh://kumar@dev/vol2/svn/etl/tags/PR28.1 from "
                        "svn+ssh://kumar@dev/vol2/svn/etl/branches/PR28'")],
            ])
        
        branch.tag('PR28.1')
        assert branch.execute.finished
        
    @nose.tools.raises(SVException)
    def test_createtag_fails_if_exists(self):
        branch = Branch(svn_info=fixtures.info_merged_forward)
        branch._svn_status = fixtures.status_clean
        branch._tags = ['some_tag']
        branch.createtag('some_tag')

class TestRebase(object):

    def setup(self):
        self.branch = Branch(svn_info=fixtures.rebase_inferred_parent.info)
        self.branch._svn_log = fixtures.rebase_inferred_parent.log
        self.branch._svn_status = fixtures.rebase_inferred_parent.status
        self.branch._branches = [
            ['jquery.1', 'jquery.2', 'some_other_branch', 'some_other_branch.1'],
            ['jquery.1', 'jquery.2', 'some_other_branch', 'some_other_branch.1'],
            # simulate new branches after copy command :
            ['jquery.1', 'jquery.2', 'jquery.3', 'some_other_branch', 'some_other_branch.1']]


    def test_rebase_inferred_parent(self):
        self.branch.execute = mock_execute(
            [
                ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/branches/some_other_branch.1', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.3', '-m', '"creating branch jquery.3"'],
                ['svn', 'switch', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.3'],
                ['svn', 'revert', '-R', '.'],
                ['svn', 'merge', '-r4:HEAD', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.2'],
                ['svn', 'up'],
            ])

        self.branch.rebase()
    

class TestBranch_Log(object):

    def test_single_log(self):
        branch = Branch(svn_info=fixtures.info)
        branch._branches = [['monkey']]
        branch.execute = mock_execute([
            ['svn', 'log', '-v', '--stop-on-copy'],
            ])
        branch.log()

    def test_rebase_log(self):
        branch = Branch(svn_info=fixtures.info_merged_forward)
        branch._branches = [['jquery.1', 'jquery.2', 'jquery.3', 'monkey']]
        branch.execute = mock_execute([
            ['svn', 'log', '-v', '--stop-on-copy', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.3'],
            ['svn', 'log', '-v', '--stop-on-copy', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.2'],
            ['svn', 'log', '-v', '--stop-on-copy', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.1'],
            ])
        branch.log()
        assert branch.execute.finished

class TestBranch_Update(object):

    def test_trunk(self):
        branch = Branch(svn_info=fixtures.info)
        branch._branches = [['jquery.1', 'jquery.2', 'monkey']]
        branch.execute = mock_execute([
            ['svn', 'up'],
            ])
        branch.update()
        assert branch.execute.finished        

    def test_basic(self):
        branch = Branch(svn_info=fixtures.info_merged_forward)
        branch._branches = [['jquery.1', 'jquery.2', 'monkey']]
        branch.execute = mock_execute([
            ['svn', 'up'],
            ])

        branch.update()
        assert branch.execute.finished

    def test_switches_to_latest(self):
        branch = Branch(svn_info=fixtures.info_merged_forward)
        branch._branches = [
            ['jquery.1', 'jquery.2', 'jquery.3', 'monkey'],
            ['jquery.1', 'jquery.2', 'jquery.3', 'monkey']]
        branch._svn_status = fixtures.status_clean
        branch.execute = mock_execute([
            ['svn', 'switch', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.3'],
            ['svn', 'revert', '-R', '.']
            ])

        branch.update()
        assert branch.execute.finished

    def test_switching_does_not_revert_on_dirty(self):
        branch = Branch(svn_info=fixtures.info_merged_forward, ignore_modifications=True)
        branch._branches = [
            ['jquery.1', 'jquery.2', 'jquery.3', 'monkey'],
            ['jquery.1', 'jquery.2', 'jquery.3', 'monkey']]
        branch._svn_status = fixtures.status_changes
        branch.execute = mock_execute([
            ['svn', 'switch', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.3']
            ])

        branch.update()
        assert branch.execute.finished

class TestReposLayout(object):    
    def test_one_project_layout(self):
        class branch:
            path = "trunk/moozapper/iozinialator.h"
            
        self.repos = ReposLayout(branch)
        eq_(self.repos.base_path, "")
        eq_(self.repos.branch("trunk/moozapper/iozinialator.h"), "iozinialator.h")
        eq_(self.repos.trunk_path(), "trunk")
        eq_(self.repos.branches_base_path(), "branches")
        eq_(self.repos.tags_base_path(), "tags")
    
    def test_multi_project_layout(self):
        class branch:
            path = "fooz/branches/moozapper/iozinialator.h"
        
        self.repos = ReposLayout(branch)
        eq_(self.repos.base_path, "fooz")
        eq_(self.repos.branch("fooz/branches/moozapper/iozinialator.h"), "iozinialator.h")
        eq_(self.repos.trunk_path(), "fooz/trunk")
        eq_(self.repos.branches_base_path(), "fooz/branches")
        eq_(self.repos.tags_base_path(), "fooz/tags")
        
    def test_custom_project_layout(self):
        class branch:
            path = "web2.0/snazzle/tools/trunk/fooz/foozinator.js"

        self.repos = ReposLayout(branch)
        eq_(self.repos.base_path, "web2.0/snazzle/tools")
        eq_(self.repos.trunk_path(), "web2.0/snazzle/tools/trunk")
        eq_(self.repos.branches_base_path(), "web2.0/snazzle/tools/branches")
        eq_(self.repos.tags_base_path(), "web2.0/snazzle/tools/tags")
        
    def test_fake_out_layout(self):
        class branch:
            path = "foo/bar/trunk/bizbar/trunk/trunkinator.php"

        self.repos = ReposLayout(branch)
        eq_(self.repos.base_path, "foo/bar")

    @raises(SVException)
    def test_non_standard_project_layout(self):
        class branch:
            path = "sweedish/tagz/rel_0_1_2/jorn/yander.taz"

        self.repos = ReposLayout(branch)    

