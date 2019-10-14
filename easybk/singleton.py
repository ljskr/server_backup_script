"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-11
"""

# 单例模式集锦


def singleton(cls, *args, **kw):
    """
    装饰器模式，使用方法：
    @singleton
    class Myclass()
    """
    instance = {}

    def _singleton():
        if cls not in instance:
            instance[cls] = cls(*args, **kw)
        return instance[cls]
    return _singleton


class Singleton():
    """
    通过__new__实现单例，使用方法：（直接继承）
    class Myclass(Singleton)
    """
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance


class Singleton2(type):
    """
    通过__metaclass__实现单例，使用方法：
    class Myclass(object)
        __metaclass__ = Singleton2
    """
    def __init__(cls, name, bases):
        super(Singleton2, cls).__init__(name, bases)
        cls._instance = None

    def __call__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = super(Singleton2, cls).__call__(*args, **kw)
        return cls._instance
