from ..fixtures import fixture_with_commands
from ..testcases import DustyIntegrationTestCase

class TestCommandFile(DustyIntegrationTestCase):
    def setUp(self):
        super(TestCommandFile, self).setUp()
        fixture_with_commands()
        self.run_command('bundles activate bundle-a')

    def tearDown(self):
        try:
            self.run_command('stop')
        except:
            pass
        self.remove_container('appa')
        super(TestCommandFile, self).tearDown()

    def test_once_is_run_once(self):
        self.run_command('up')
        self.assertFileInContainer('appa', '/once_test_file')
        self.assertFileContentsInContainer('appa', '/once_test_file', 'once ran\n')
        self.run_command('restart appa')
        self.assertFileContentsInContainer('appa', '/once_test_file', 'once ran\n')

    def test_always_is_run_always(self):
        self.run_command('up')
        self.assertFileInContainer('appa', '/always_test_file')
        self.assertFileContentsInContainer('appa', '/always_test_file', 'always ran\n')
        self.run_command('restart appa')
        self.assertFileContentsInContainer('appa', '/always_test_file', 'always ran\nalways ran\n')

    def test_once_to_stdout(self):
        self.run_command('up')
        output = self.run_command('logs appa')
        print output
        self.assertTrue('once ran' in output)

    def test_always_to_stdout(self):
        self.run_command('up')
        output = self.run_command('logs appa')
        print output
        self.assertTrue('always ran' in output)

    def test_once_output_is_logged(self):
        self.run_command('up')
        self.assertFileContentsInContainer('appa', '/var/log/dusty_once_fn.log', 'once ran\n')

    def test_once_stops_on_error(self):
        fixture_with_commands(once_fail=True)
        self.run_command('up')
        output = self.run_command('logs appa')
        print output
        self.assertTrue('once starting' in output)
        self.assertInSameLine(output, 'random-command', 'not found')
        self.assertFalse('once ran' in output)
        self.assertContainerIsNotRunning('appa')

    def test_always_stops_on_error(self):
        fixture_with_commands(always_fail=True)
        self.run_command('up')
        output = self.run_command('logs appa')
        print output
        self.assertTrue('once ran' in output)
        self.assertTrue('always starting' in output)
        self.assertInSameLine(output, 'random-command', 'not found')
        self.assertFalse('always ran' in output)
        self.assertContainerIsNotRunning('appa')
