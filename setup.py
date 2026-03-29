from setuptools import setup, find_packages

setup(
    name="computecfo",
    version="1.1.0",
    description="Your AI Financial Officer — Track, analyze, and optimize LLM API spending",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="SilentFleetKK",
    url="https://github.com/SilentFleetKK/computecfo",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[],
    extras_require={
        "api": ["fastapi>=0.100", "uvicorn>=0.20"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
    ],
    keywords="ai, llm, cost, tracking, budget, roi, claude, openai, computecfo, agent",
)
