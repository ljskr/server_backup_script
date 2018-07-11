# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-11

# 单例模式集锦

"""
装饰器模式，使用方法：
@singleton
class Myclass()
"""
def singleton(cls, *args, **kw):
    instance={}
    def _singleton():
        if cls not in instance:
            instance[cls] = cls(*args, **kw)
        return instance[cls]
    return _singleton

"""
通过__new__实现单例，使用方法：（直接继承）
class Myclass(Singleton)
"""
class Singleton(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance

"""
通过__metaclass__实现单例，使用方法：
class Myclass(object)
    __metaclass__ = Singleton2
"""
class Singleton2(type):
    def __init__(cls, name, bases, dict):
        super(Singleton2, cls).__init__(name, bases, dict)
        cls._instance = None
    def __call__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = super(Singleton2, cls).__call__(*args, **kw)
        return cls._instance
