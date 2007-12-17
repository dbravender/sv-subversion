from lxml import etree
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

parse = lambda xml: etree.parse(StringIO(xml))

info = parse('''<?xml version="1.0"?>
<info>
<entry
kind="dir"
path="."
revision="18799">
<url>svn+ssh://dev/vol2/svn/monkey/trunk</url>
<repository>
<root>svn+ssh://dev/vol2/svn</root>
<uuid>d3f15640-29ef-0310-be8a-e17a052a3da3</uuid>
</repository>
<wc-info>
<schedule>normal</schedule>
</wc-info>
<commit
revision="18732">
<author>dbravender</author>
<date>2007-08-01T20:46:18.133879Z</date>
</commit>
</entry>
</info>''')

info_merged_forward = parse('''<?xml version="1.0"?>
<info>
<entry
kind="dir"
path="."
revision="18799">
<url>svn+ssh://dev/vol2/svn/monkey/branches/jquery.2</url>
<repository>
<root>svn+ssh://dev/vol2/svn</root>
<uuid>d3f15640-29ef-0310-be8a-e17a052a3da3</uuid>
</repository>
<wc-info>
<schedule>normal</schedule>
</wc-info>
<commit
revision="18732">
<author>dbravender</author>
<date>2007-08-01T20:46:18.133879Z</date>
</commit>
</entry>
</info>''')

log = parse('''<?xml version="1.0"?>
<log>
<logentry
   revision="18497">
<author>dbravender</author>
<date>2007-07-25T15:59:48.783051Z</date>
<msg>some comment on page load</msg>
</logentry>
<logentry
   revision="18496">
<author>dbravender</author>
<date>2007-07-25T15:55:15.863284Z</date>
<msg>creating a branch for adding jquery or replacing mochikit with jquery</msg>
</logentry>
</log>''')

status_changes = parse('''<?xml version="1.0"?>
<status>
<target
   path=".">
<entry
   path="test.pyc">
<wc-status
   props="none"
   item="unversioned">
</wc-status>
</entry>
<entry
   path="shellLocal.sh">
<wc-status
   props="none"
   item="modified"
   revision="18579">
<commit
   revision="18403">
<author>cmcavoy</author>
<date>2007-07-20T20:23:58.307906Z</date>
</commit>
</wc-status>
</entry>
</target>
</status>''')

status_clean = parse('''<?xml version="1.0"?>
<status>
<target
   path=".">
</target>
</status>''')

log_trunk_branch_parent = parse('''<?xml version="1.0"?>
<log>
<logentry
   revision="8">
<author>dbravender</author>
<date>2007-08-12T05:32:38.538458Z</date>
<paths>
<path
   action="A">/branches/brass_monkey/that_funky_monkey</path>
</paths>
<msg>insane
</msg>
</logentry>
<logentry
   revision="4">
<author>dbravender</author>
<date>2007-08-12T05:22:02.975050Z</date>
<paths>
<path
   copyfrom-path="/autoleads/trunk"
   copyfrom-rev="3"
   action="A">/branches/brass_monkey</path>
</paths>
<msg>awesome
</msg>
</logentry>
</log>''')

log_non_trunk_branch_parent = parse('''<?xml version="1.0"?>
<log>
<logentry
   revision="8">
<author>dbravender</author>
<date>2007-08-12T05:32:38.538458Z</date>
<paths>
<path
   action="A">/branches/brass_monkey/that_funky_monkey</path>
</paths>
<msg>insane
</msg>
</logentry>
<logentry
   revision="4">
<author>dbravender</author>
<date>2007-08-12T05:22:02.975050Z</date>
<paths>
<path
   copyfrom-path="/autoleads/branches/some_other_branch"
   copyfrom-rev="3"
   action="A">/branches/brass_monkey</path>
</paths>
<msg>awesome
</msg>
</logentry>
</log>''')

log_non_trunk_branch_parent_with_copies = parse('''<?xml version="1.0"?>
<log>
<logentry
   revision="8">
<author>dbravender</author>
<date>2007-08-12T05:32:38.538458Z</date>
<paths>
<path
   action="A">/branches/brass_monkey/that_funky_monkey</path>
</paths>
<msg>insane
</msg>
</logentry>
<logentry
   revision="7">
<author>dbravender</author>
<date>2007-08-12T05:32:38.538458Z</date>
<paths>
<path
   copyfrom-path="/branches/copper_monkey/the_first_monkey"
   copy-from-rev="6"
   action="A">/branches/brass_monkey/the_first_monkey</path>
</paths>
<msg>insane
</msg>
</logentry>

<logentry
   revision="4">
<author>dbravender</author>
<date>2007-08-12T05:22:02.975050Z</date>
<paths>
<path
   copyfrom-path="/autoleads/branches/some_other_branch"
   copyfrom-rev="3"
   action="A">/branches/brass_monkey</path>
</paths>
<msg>awesome
</msg>
</logentry>
</log>''')

ls_before_changes = parse('''<?xml version="1.0"?>
<lists>
<list
   path="https://bravender.us/svn/public/sv/trunk">
<entry
   kind="file">
<name>fixtures.py</name>
<size>2969</size>
<commit
   revision="2">
<author>dbravender</author>
<date>2007-08-12T22:24:49.248816Z</date>
</commit>
</entry>
<entry
   kind="file">
<name>sv</name>
<size>10</size>
<commit
   revision="2">
<author>dbravender</author>
<date>2007-08-12T22:24:49.248816Z</date>
</commit>
</entry>
<entry
   kind="file">
<name>sv.py</name>
<size>10134</size>
<commit
   revision="2">
<author>dbravender</author>
<date>2007-08-12T22:24:49.248816Z</date>
</commit>
</entry>
<entry
   kind="file">
<name>test_sv.py</name>
<size>4533</size>
<commit
   revision="2">
<author>dbravender</author>
<date>2007-08-12T22:24:49.248816Z</date>
</commit>
</entry>
</list>
</lists>''')

ls_after_changes = parse('''<?xml version="1.0"?>
<lists>
<list
   path=".">
<entry
   kind="file">
<name>added_file</name>
<size>38</size>
<commit
   revision="7">
<author>dbravender</author>
<date>2007-08-12T22:56:50.430839Z</date>
</commit>
</entry>
<entry
   kind="file">
<name>fixtures.py</name>
<size>2969</size>
<commit
   revision="2">
<author>dbravender</author>
<date>2007-08-12T22:24:49.248816Z</date>
</commit>
</entry>
<entry
   kind="file">
<name>sv</name>
<size>10</size>
<commit
   revision="2">
<author>dbravender</author>
<date>2007-08-12T22:24:49.248816Z</date>
</commit>
</entry>
<entry
   kind="file">
<name>sv.py</name>
<size>10246</size>
<commit
   revision="4">
<author>dbravender</author>
<date>2007-08-12T22:37:34.237015Z</date>
</commit>
</entry>
<entry
   kind="file">
<name>test_sv.py</name>
<size>4533</size>
<commit
   revision="2">
<author>dbravender</author>
<date>2007-08-12T22:24:49.248816Z</date>
</commit>
</entry>
</list>
</lists>''')

class tag_from_latest_branch:
    """you are in a branch named jquery.1"""
    info = parse('''<?xml version="1.0"?>
<info>
<entry
kind="dir"
path="."
revision="18799">
<url>svn+ssh://dev/vol2/svn/monkey/branches/jquery.2</url>
<repository>
<root>svn+ssh://dev/vol2/svn</root>
<uuid>d3f15640-29ef-0310-be8a-e17a052a3da3</uuid>
</repository>
<wc-info>
<schedule>normal</schedule>
</wc-info>
<commit
revision="18732">
<author>dbravender</author>
<date>2007-08-01T20:46:18.133879Z</date>
</commit>
</entry>
</info>''')
    
    log = parse('''<?xml version="1.0"?>
<log>
<logentry
   revision="8">
<author>dbravender</author>
<date>2007-08-12T05:32:38.538458Z</date>
<paths>
<path
   action="A">/branches/brass_monkey/that_funky_monkey</path>
</paths>
<msg>insane
</msg>
</logentry>
<logentry
   revision="4">
<author>dbravender</author>
<date>2007-08-12T05:22:02.975050Z</date>
<paths>
<path
   copyfrom-path="/autoleads/trunk"
   copyfrom-rev="3"
   action="A">/branches/brass_monkey</path>
</paths>
<msg>awesome
</msg>
</logentry>
</log>''')
    
    status = parse('''<?xml version="1.0"?>
<status>
<target
   path=".">
</target>
</status>''')


class tag_from_trunk:
    """you are in a branch named jquery.1"""
    info = parse('''<?xml version="1.0"?>
<info>
<entry
kind="dir"
path="."
revision="18799">
<url>svn+ssh://dev/vol2/svn/monkey/trunk</url>
<repository>
<root>svn+ssh://dev/vol2/svn</root>
<uuid>d3f15640-29ef-0310-be8a-e17a052a3da3</uuid>
</repository>
<wc-info>
<schedule>normal</schedule>
</wc-info>
<commit
revision="18732">
<author>dbravender</author>
<date>2007-08-01T20:46:18.133879Z</date>
</commit>
</entry>
</info>''')
    
    log = parse('''<?xml version="1.0"?>
<log>
<logentry
   revision="8">
<author>dbravender</author>
<date>2007-08-12T05:32:38.538458Z</date>
<paths>
<path
   action="A">/branches/brass_monkey/that_funky_monkey</path>
</paths>
<msg>insane
</msg>
</logentry>
<logentry
   revision="4">
<author>dbravender</author>
<date>2007-08-12T05:22:02.975050Z</date>
<paths>
<path
   copyfrom-path="/autoleads/trunk"
   copyfrom-rev="3"
   action="A">/branches/brass_monkey</path>
</paths>
<msg>awesome
</msg>
</logentry>
</log>''')
    
    status = parse('''<?xml version="1.0"?>
<status>
<target
   path=".">
</target>
</status>''')

class rebase_inferred_parent:
    info = parse('''<?xml version="1.0"?>
<info>
<entry
kind="dir"
path="."
revision="18799">
<url>svn+ssh://dev/vol2/svn/monkey/branches/jquery.2</url>
<repository>
<root>svn+ssh://dev/vol2/svn</root>
<uuid>d3f15640-29ef-0310-be8a-e17a052a3da3</uuid>
</repository>
<wc-info>
<schedule>normal</schedule>
</wc-info>
<commit
revision="18732">
<author>dbravender</author>
<date>2007-08-01T20:46:18.133879Z</date>
</commit>
</entry>
</info>''')
    
    log = parse('''<?xml version="1.0"?>
<log>
<logentry
   revision="8">
<author>dbravender</author>
<date>2007-08-12T05:32:38.538458Z</date>
<paths>
<path
   action="A">/branches/brass_monkey/that_funky_monkey</path>
</paths>
<msg>insane
</msg>
</logentry>
<logentry
   revision="4">
<author>dbravender</author>
<date>2007-08-12T05:22:02.975050Z</date>
<paths>
<path
   copyfrom-path="/autoleads/branches/some_other_branch"
   copyfrom-rev="3"
   action="A">/branches/brass_monkey</path>
</paths>
<msg>awesome
</msg>
</logentry>
</log>''')
    
    status = parse('''<?xml version="1.0"?>
<status>
<target
   path=".">
</target>
</status>''')
    

class from_branch_with_R:
    """you are in a branch named PR28, created from 
    trunk with an extra "R" action on setup.py
    
    """
    info = parse('''<?xml version="1.0"?>
<info>
<entry
   kind="dir"
   path="."
   revision="22572">
<url>svn+ssh://kumar@dev/vol2/svn/etl/branches/PR28</url>
<repository>
<root>svn+ssh://kumar@dev/vol2/svn</root>
<uuid>d3f15640-29ef-0310-be8a-e17a052a3da3</uuid>
</repository>
<wc-info>
<schedule>normal</schedule>
</wc-info>
<commit
   revision="22564">
<author>kumar</author>
<date>2007-11-20T22:48:11.764105Z</date>
</commit>
</entry>
</info>''')
    
    status = parse('''<?xml version="1.0"?>
<status>
<target
   path=".">
</target>
</status>''')
    
    # here is the culprit, the "R" action:
    log = parse('''<?xml version="1.0"?>
<log>
<logentry
   revision="21984">
<author>kumar</author>
<date>2007-11-07T23:09:25.895352Z</date>
<paths>
<path
   copyfrom-path="/etl/trunk"
   copyfrom-rev="21982"
   action="A">/etl/branches/PR28</path>
<path
   copyfrom-path="/etl/trunk/setup.py"
   copyfrom-rev="21983"
   action="R">/etl/branches/PR28/setup.py</path>
</paths>
<msg>cutting PR28 branch from trunk
</msg>
</logentry>
</log>''')
