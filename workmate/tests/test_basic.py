def add(a: int, b: int) -> int:
    return a + b

#assert 断言：判断
#test_开头的文件名和函数名，让pytest按照默认约定识别测试
def test_add():
    result = add(2, 3)

    assert result == 5