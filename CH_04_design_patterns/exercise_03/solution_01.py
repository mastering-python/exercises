class Borg:

    def __new__(cls):
        if not hasattr(cls, '_state'):
            cls._state = {}
        instance = super(Borg, cls).__new__(cls)
        instance.__dict__ = cls._state
        return instance


class SubBorg(Borg):
    pass


class SubBorg2(Borg):
    pass


def main():
    a = SubBorg()
    b = SubBorg()
    c = SubBorg2()
    a.attr = 10
    assert hasattr(b, 'attr') and b.attr == 10
    assert not hasattr(c, 'attr')


if __name__ == '__main__':
    main()
