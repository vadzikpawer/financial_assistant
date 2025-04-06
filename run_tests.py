import unittest
import coverage
import sys

def run_tests_with_coverage():
    """Run tests with coverage report"""
    # Start coverage measurement
    cov = coverage.Coverage(
        source=['app', 'models', 'routers', 'services'],
        omit=['*/__pycache__/*', '*/tests/*']
    )
    cov.start()

    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    # Stop coverage measurement
    cov.stop()
    cov.save()

    # Print coverage report
    print('\nCoverage Summary:')
    cov.report()

    # Generate HTML report
    cov.html_report(directory='coverage_report')
    print('HTML coverage report generated in coverage_report directory')

    # Return exit code based on test result
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests_with_coverage())
