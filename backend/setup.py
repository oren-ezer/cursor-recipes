from setuptools import setup, find_packages

setup(
    name="cursor-recipes",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "supabase",
        "python-dotenv",
        "pydantic",
        "pydantic-settings"
    ],
) 