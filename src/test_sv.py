from sv import Branch
import fixtures

def dont_execute(cls, command, *args, **kwargs):
    raise Exception, 'Tried to execute %s' % command

# we don't want the tests to _ever_ execute commands
Branch.execute = dont_execute

def mock_execute(expected_commands):
    def execute(command, *args, **kwargs):
        assert command == expected_commands[execute.count]
        execute.count += 1
    execute.count = 0
    return execute

class TestBranch(object):
    def setup(self):
        # svn info since is needed during init
        self.branch = Branch(svn_info=fixtures.info)
    
    def test_info(self):
        assert self.branch.root == 'svn+ssh://dev/vol2/svn'
        assert self.branch.path == 'monkey/trunk'
        assert self.branch.revision == 18799
        assert self.branch.project == 'monkey'
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
        assert self.branch.changed_files
    
    def test_revert(self):
        self.branch.execute = mock_execute([['svn', 'revert', '-R', '.']])
        self.branch.revert()
        
    def test_merge(self): 
        self.branch.execute = mock_execute([['svn', 'merge', '-r18496:HEAD', 'svn+ssh://dev/vol2/svn/monkey/branches/some_other_branch']])
        self.branch.merge('some_other_branch', '18496', 'HEAD')
     
        self.sv = Branch(svn_info=fixtures.info_merged_forward)
        self.branch.execute = mock_execute([['svn', 'merge', '-r18496:HEAD', 'svn+ssh://dev/vol2/svn/monkey/branches/some_other_branch']])
        self.branch.merge('some_other_branch', '18496', 'HEAD')
        
    def test_create(self):
        self.branch._svn_log = fixtures.log_trunk_branch_parent
        self._branches = ['some_other_branch']
        self.branch.execute = mock_execute([['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/trunk', 'svn+ssh://dev/vol2/svn/monkey/branches/test_branch', '-m', '"creating branch test_branch"']])
        self.branch.create('test_branch')
    
    def test_create_different_parent(self):
        self.branch = Branch(svn_info=fixtures.info_merged_forward)
        self.branch._svn_log = fixtures.log_non_trunk_branch_parent
        self.branch._branches = ['jquery.1', 'jquery.2', 'jquery.3', 'some_other_branch', 'some_other_branch.1']
        self.branch.execute = mock_execute([['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/branches/some_other_branch.1', 'svn+ssh://dev/vol2/svn/monkey/branches/test_branch', '-m', '"creating branch test_branch"']])
        self.branch.create('test_branch')
    
    def test_rebase_inferred_parent(self):
        self.branch = Branch(svn_info=fixtures.info_merged_forward)
        self.branch._svn_log = fixtures.log_non_trunk_branch_parent
        self.branch._svn_status = fixtures.status_clean
        self.branch._branches = ['jquery.1', 'jquery.2', 'jquery.3', 'some_other_branch', 'some_other_branch.1']
        self.branch.execute = mock_execute(
            [
                ['svn', 'cp', 'svn+ssh://dev/vol2/svn/monkey/branches/some_other_branch.1', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.3', '-m', '"creating branch jquery.3"'],
                ['svn', 'switch', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.3'],
                ['svn', 'revert', '-R', '.'],
                ['svn', 'merge', '-r4:HEAD', 'svn+ssh://dev/vol2/svn/monkey/branches/jquery.2'],
                ['svn', 'up'],
            ])

        self.branch.rebase()
    
    def test_ls_diff(self):
        assert self.branch.ls_diff(fixtures.ls_before_changes, fixtures.ls_after_changes) == ['added_file', 'sv.py']
        
