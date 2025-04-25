import os


def pytest_generate_tests():
    os.environ["BUCKET"] = "fake-bucket"
    os.environ["CF_API_URL"] = "http://cf.localhost"
    os.environ["UAA_API_URL"] = "http://uaa.localhost"
    os.environ["UAA_CLIENT_ID"] = "fake-client"
    os.environ["UAA_CLIENT_SECRET"] = "fake-secret"
