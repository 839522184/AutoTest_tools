import pytest
import allure


class Test01():

    def setup_method(self, method):
        print(" 用例 *** 后置 ***")

    def teardown_method(self):
        print(" 用例 *** 后置 ***")

    @pytest.mark.new
    def test_01(self):
        """
        test_01
        :return:
        """
        try:
            assert False, "测试失败"
        except Exception as e:
            raise e

    def test_02(self):
        """
        test_02
        :return:
        """
        a = 1
        b = 2
        assert a + b == 3

    @allure.story("模块名-allure测试")
    @allure.description("用例标题")
    @allure.severity("P0")
    def test_allure(self):
        print("allure test")
