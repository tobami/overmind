import unittest
import test_provisioning


def suite():
    provisioning = test_provisioning.suite()
    return unittest.TestSuite([provisioning])
