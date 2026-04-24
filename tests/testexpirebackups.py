"""
Created on 01.04.2022

@author: wf
"""

import io
import re
import unittest
from contextlib import redirect_stderr

import expirebackups.expire
from expirebackups.expire import Expiration, ExpireBackups


class TestExpireBackups(unittest.TestCase):
    """
    test Expire Backups
    """

    def setUp(self):
        self.debug = False
        pass

    def tearDown(self):
        pass

    def doTestPattern(
        self,
        days: int,
        weeks: int,
        months: int,
        years: int,
        failMsg: str,
        expectedMatch: str,
    ):
        """
        test the given pattern
        """
        try:
            _expiration = Expiration(days=days, weeks=weeks, months=months, years=years)
            self.fail(failMsg)
        except Exception as ex:
            self.assertTrue(re.match(expectedMatch, str(ex)))

    def testCreateTestFiles(self):
        """
        test creating test files to be expired
        """
        ext = ".tst"
        testFile = ExpireBackups.createTestFile(10, ext=ext)
        debug = self.debug
        debug = True
        if debug:
            print(testFile)
        path, backupFiles = ExpireBackups.createTestFiles(20, ext=ext)
        if debug:
            print(path)
        for i, backupFile in enumerate(backupFiles):
            if debug:
                print(f"{i + 1:3d}:{backupFile.getAgeInDays():3.1f}:{testFile}")
            backupFile.delete()

    def testSubDayAge(self):
        """
        test that files less than 24h apart get distinct ages - fixes #11
        """
        from expirebackups.expire import BackupFile

        ext = ".sdt"
        f1 = ExpireBackups.createTestFile(0.5, ext=ext)
        f2 = ExpireBackups.createTestFile(0.9, ext=ext)
        bf1 = BackupFile(f1)
        bf2 = BackupFile(f2)
        self.assertNotEqual(round(bf1.ageInDays, 1), round(bf2.ageInDays, 1))
        bf1.delete()
        bf2.delete()

    def testCronDriftRegression(self):
        """
        test that cron drift (backup slightly <24h apart) does not cause the
        middle daily file to be expired - regression for #11 follow-up.

        Scenario: today's backup ~0.02 days old, yesterday's ~0.99 days old
        (cron fired a few minutes earlier than prior day), and an older
        backup ~3.00 days old. With days=2 the oldest must go, both recent
        files must be kept.
        """
        from expirebackups.expire import BackupFile

        ext = ".cdr"
        ages = [0.02, 0.99, 3.00]
        paths = [ExpireBackups.createTestFile(a, ext=ext) for a in ages]
        files = [BackupFile(p) for p in paths]
        try:
            expiration = Expiration(
                days=2, weeks=0, months=0, years=0, minFileSize=0
            )
            result = expiration.applyRules(files, verbose=False)
            byPath = {bf.filePath: bf for bf in result}
            self.assertFalse(byPath[paths[0]].expire, "newest (0.02d) must be kept")
            self.assertFalse(byPath[paths[1]].expire, "middle (0.99d) must be kept")
            self.assertTrue(byPath[paths[2]].expire, "oldest (3.00d) must be expired")
        finally:
            for bf in files:
                bf.delete()

    def testExpireBackus(self):
        """
        test expiration of backups
        """
        # ebt= expire backup test
        ext = ".ebt"
        numberOfFiles = (
            expirebackups.expire.defaultDays
            + expirebackups.expire.defaultWeeks * 7
            + expirebackups.expire.defaultMonths * 28
        )
        path, _backupFiles = ExpireBackups.createTestFiles(numberOfFiles, ext=ext)
        eb = ExpireBackups(rootPath=path, ext=ext)
        # test files are only touched so allow minimum fileSize 0
        eb.expiration.minFileSize = 0
        debug = self.debug
        # debug=True
        eb.expiration.debug = debug
        # show=True
        showLimit = 38
        eb.doexpire(withDelete=True, showLimit=showLimit)

    def testPatterns(self):
        """
        test different patterns for being valid
        """
        patterns = [
            (-1, 0, 0, 0, "days"),
            (0, -1, 0, 0, "weeks"),
            (0, 0, -1, 0, "months"),
            (0, 0, 0, -1, "years"),
        ]
        for days, weeks, months, years, name in patterns:
            failMsg = f"pattern for {name} failed"
            expectedMatch = rf"^-1 {name} is invalid - {name} must be >=0$"
            self.doTestPattern(days, weeks, months, years, failMsg, expectedMatch)

    def testArgs(self):
        """
        test Arguments
        """
        args = ["a", "b"]
        result = None
        stderr = io.StringIO()
        try:
            with redirect_stderr(stderr):
                expirebackups.expire.main(args)
            self.fail("There should be a System Exception")
        except SystemExit as se:
            self.assertEqual(2, se.code)
            result = stderr.getvalue()
            if self.debug:
                print(result)
            self.assertTrue("usage:" in result)
            pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
