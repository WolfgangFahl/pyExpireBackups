'''
Created on 01.04.2022

@author: wf
'''
import unittest
from contextlib import redirect_stderr
import io
from expirebackups.expire import ExpireBackups
import expirebackups.expire

class TestExpireBackups(unittest.TestCase):
    '''
    test Expire Backups
    '''

    def setUp(self):
        self.debug=False
        pass


    def tearDown(self):
        pass


    def testArgs(self):
        '''
        test Arguments
        '''
        args=["a","b"];
        result=None
        stderr = io.StringIO()
        try:
            with redirect_stderr(stderr):
                expirebackups.expire.main(args)
            self.fail("There should be a System Exception")
        except SystemExit as se:
            self.assertEqual(2,se.code)
            result = stderr.getvalue()
            if self.debug:
                print(result)
            self.assertTrue("usage:" in result)
            pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()