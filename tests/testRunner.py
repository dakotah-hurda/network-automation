# tests/test_script1.py
import unittest

def run_tests():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('', pattern='test_*.py')
    test_runner = unittest.TextTestRunner()
    return test_runner.run(test_suite)

if __name__ == '__main__':
    # unittest.main()
    
    run_tests()