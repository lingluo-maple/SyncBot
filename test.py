import unittest

class ConfigTest(unittest.TestCase):
    def test_getQQGroup(self):
        from config import ForwardGroupConfig
        groups = ForwardGroupConfig(
            {
                123456789012: -1001234567890
                }
            )
        self.assertTrue(groups.getQQGroup(-1001234567890) == 123456789012)

    def test_getTGGroup(self):
        from config import ForwardGroupConfig
        groups = ForwardGroupConfig(
            {
                123456789012: -1001234567890
            }
        )
        self.assertTrue(groups.getTGGroup(123456789012) == -1001234567890)

if __name__ == "__main__":
    unittest.main()