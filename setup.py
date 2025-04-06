from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="finassistant",
    version="1.0.0",
    description="Персональный финансовый помощник с AI-рекомендациями",
    author="Replit AI",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=requirements,
)
