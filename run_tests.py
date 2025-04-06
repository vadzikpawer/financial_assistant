import pytest
import coverage
import sys


def run_tests_with_coverage():
    """Run tests with coverage report"""
    # Start coverage measurement
    cov = coverage.Coverage(
        source=["app", "models", "routers", "services"],
        omit=["*/__pycache__/*", "*/tests/*"],
    )
    cov.start()

    # Run tests with pytest
    exit_code = pytest.main(["-xvs", "tests"])

    # Stop coverage measurement
    cov.stop()
    cov.save()

    # Print coverage report
    print("\nCoverage Summary:")
    cov.report()

    # Generate HTML report
    cov.html_report(directory="coverage_report")
    print("HTML coverage report generated in coverage_report directory")

    # Return exit code from pytest
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests_with_coverage())
