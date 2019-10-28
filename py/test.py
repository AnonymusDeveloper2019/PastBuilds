import unittest
from checkBuildHistory import BuildChecker
from buildHelper import NO_BUILD_MESSAGE
from utils import DefaultProcessManager
import os
import re

try: 
    import parameterized
except ImportError:
    print("Lib parameterized not local available")
    import pip
    cmd = "pip install parameterized"
    os.system(cmd)

from parameterized import parameterized

def getLog(path):
    with open(path,"r") as f:
        return f.read()

test = [
        ('NoBuildSystemTest',                   'Closure-test-1-config.json',   '7e0d71b3', 'FAIL',     NO_BUILD_MESSAGE),
        ('SuccessBuildTest-Closure',            'Closure-test-2-config.json',   '49e9565f', 'SUCCESS',  'BUILD SUCCESS'),
        ('FailedBuildTest',                     'Closure-test-3-config.json',   '86e26932', 'FAIL',     'BUILD FAILED'),
        ('SuccessBuildTest_DeepConfigFile',     'Time-test-1-config.json',      '0f951f39', 'SUCCESS',  'BUILD SUCCESS'),
        ('Case 1',                              'Math-test-1-config.json',      '0da657a6', 'SUCCESS',  'BUILD SUCCESS'), 
        ('Case 2',                              'Lang-test-1-config.json',      '687b2e62', 'SUCCESS',  'BUILD SUCCESS'),
        ('Case 2.1',                            'Lang-test-2-config.json',      '5ac897ad', 'SUCCESS',  'BUILD SUCCESS')
    ]

class CheckBuildTest(unittest.TestCase):

    @parameterized.expand(test)
    def test_simple(self,name,config, commit, state, pattern):
        bcheck = BuildChecker("configFiles/_test/%s"%config, test=True)
        self.delete_path = bcheck.path
        bcheck.checkBuild()
        bcheck.finish("FINISHED EXPERIMENT SUCCESSFULLY - TEST MODE")
        commits = bcheck.csvDict
        
        # CHECK BUILD STATUS 
        self.assertEqual(commits[commit]['build'], state)

        dir_ = 'analysis/%s/experiment_0/logs/'%bcheck.config['project']

        logs = [f for f in os.listdir(dir_) if re.match(r'0-%s-attempt-\d.log'%commit, f)]

        # CHECK LOG 
        self.assertRegex(getLog(dir_+logs[-1]), pattern)
    
    def test_multi(self):
        config = "Lang-test-4-config.json"
        bcheck = BuildChecker("configFiles/_test/%s"%config, test=True)
        self.delete_path = bcheck.path
        bcheck.checkBuild()
        bcheck.finish("FINISHED EXPERIMENT SUCCESSFULLY - TEST MODE")
        commits = bcheck.csvDict
        
        # CHECK BUILD STATUS 
        self.assertEqual(commits['c745cdf5']['build'], "SUCCESS")
        self.assertEqual(commits['1161a577']['build'], "SUCCESS")
        self.assertEqual(commits['123836ed']['build'], "SUCCESS")
        self.assertEqual(commits['0bf26e0d']['build'], "SUCCESS")

        dir_ = 'analysis/%s/experiment_0/logs/'%bcheck.config['project']

        # CHECK LOGS

        self.assertRegex(getLog(dir_+"0-c745cdf5-attempt-1.log"), 'BUILD SUCCESS')
        self.assertRegex(getLog(dir_+"1-1161a577-attempt-1.log"), 'BUILD SUCCESS')
        self.assertRegex(getLog(dir_+"2-123836ed-attempt-1.log"), 'BUILD FAILURE')
        self.assertRegex(getLog(dir_+"2-123836ed-attempt-2.log"), 'BUILD SUCCESS')
        self.assertRegex(getLog(dir_+"3-0bf26e0d-attempt-1.log"), 'BUILD FAILURE')
        self.assertRegex(getLog(dir_+"3-0bf26e0d-attempt-2.log"), 'BUILD SUCCESS')

    def tearDown(self):
        DefaultProcessManager.execute("rm -rf %s"%self.delete_path)

if __name__ == '__main__':
    unittest.main(verbosity=2)
        

