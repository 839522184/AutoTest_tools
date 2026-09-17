import pytest


def pytest_addoption(parser):
    """
    pytest入参自定义
    :param parser:
    :return:
    """
    parser.addoption(
        '--udid',
        action="store", default=None,
        help="传入设备的ID")


def pytest_configure(config):
    """
    参数注册
    :param config:
    :return:
    """
    pytest.udid = config.getoption("udid")


@pytest.fixture(scope="session")
def java_setup(request):
    print("setup")
    # start_time = time.time()

    def teardown():
        print("teardown")

    request.addfinalizer(teardown)
