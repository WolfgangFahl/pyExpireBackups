'''
Created on 01.04.2022

@author: wf
'''
import unittest
from contextlib import redirect_stderr
import io
import re
from expirebackups.expire import ExpireBackups, Expiration
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
    
    def doTestPattern(self,days:int,weeks:int,months:int,years:int,failMsg:str, expectedMatch:str):
        '''
        test the given pattern
        '''
        try:
            _expiration=Expiration(days=days,weeks=weeks,months=months,years=years)
            self.fail(failMsg)
        except Exception as ex:
            self.assertTrue(re.match(expectedMatch,str(ex)))
    
    def testPatterns(self):
        '''
        test different patterns for being valid
        '''
        patterns=[
            (0,1,1,1,"pattern with 0 days not allowed",r"^0 days is invalid - value must be >=1")
        ]
        for days,weeks,months,years,failMsg,expectedMatch in patterns:
            self.doTestPattern(days, weeks, months, years, failMsg, expectedMatch)


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