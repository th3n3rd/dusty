from os import path
from shutil import rmtree
from subprocess import check_output
from tempfile import mkdtemp

import git

from dusty.constants import REPOS_DIR
from ...fixtures import busybox_single_app_bundle_fixture
from ...testcases import DustyIntegrationTestCase


class TestReposCLI(DustyIntegrationTestCase):
    def setUp(self):
        super(TestReposCLI, self).setUp()
        busybox_single_app_bundle_fixture(num_bundles=1)
        self.set_up_fake_local_repo(path='/tmp/fake-repo-1', short_name='fake-repo-1')

    def tearDown(self):
        super(TestReposCLI, self).tearDown()
        rmtree('/tmp/fake-repo-1')

    def test_repos_list(self):
        result = self.run_command('repos list')
        self.assertInSameLine(result, 'Full Name', 'Short Name', 'Local Override')
        self.assertInSameLine(result, 'github.com/gamechanger/dusty-example-specs', 'dusty-example-specs', self.overridden_specs_path)
        self.assertInSameLine(result, 'tmp/fake-repo', 'fake-repo')

    def test_repos_override(self):
        result = self.run_command('repos list')
        self.assertInSameLine(result, 'fake-repo', '/tmp/fake-repo')
        self.assertNotInSameLine(result, 'fake-repo', '/tmp/fake-repo-1')
        self.run_command('repos override fake-repo /tmp/fake-repo-1')
        result = self.run_command('repos list')
        self.assertInSameLine(result, 'tmp/fake-repo', 'fake-repo', '/tmp/fake-repo-1')

    def test_repos_manage(self):
        self.run_command('repos override fake-repo /tmp/fake-repo-1')
        result = self.run_command('repos list')
        self.assertInSameLine(result, '/tmp/fake-repo', 'fake-repo', '/tmp/fake-repo-1')
        result = self.run_command('repos manage fake-repo')
        self.assertNotInSameLine(result, 'fake-repo', '/tmp/fake-repo-1')

    def test_repos_from(self):
        self.set_up_fake_local_repo(path='/tmp/from/fake-repo', short_name='fake-repo')
        self.run_command('repos from /tmp/from')
        result = self.run_command('repos list')
        self.assertInSameLine(result, '/tmp/fake-repo', 'fake-repo', 'tmp/from/fake-repo')
        self.run_command('repos manage /tmp/fake-repo')
        result = self.run_command('repos list')
        rmtree('/tmp/from')

    def test_repos_update(self):
        self.run_command('bundles activate busyboxa')
        git_repo = git.Repo('/tmp/fake-repo')
        check_output(['touch', '/tmp/fake-repo/foo'])
        git_repo.index.add(['/tmp/fake-repo/foo'])
        git_repo.index.commit('Second commit')
        self.assertFalse(path.isfile(path.join(REPOS_DIR, 'tmp/fake-repo/foo')))
        self.run_command('repos update')
        self.assertTrue(path.isfile(path.join(REPOS_DIR, 'tmp/fake-repo/foo')))
        rmtree('/tmp/fake-repo')
        self.set_up_fake_local_repo()
        self.run_command('repos update')
        self.run_command('bundles deactivate busyboxa')
