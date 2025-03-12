from setuptools import setup, find_packages

setup(
    name="data_dictionary_system",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "python-multipart",
        "python-dotenv",
        "openai",
        "pydantic",
    ],
) 