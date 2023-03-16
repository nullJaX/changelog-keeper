from changelog_keeper import VERSION, VERSION_PARTS


def test_module_version():
    assert len(VERSION_PARTS) == 3
    assert all(isinstance(part, int) for part in VERSION_PARTS)
    assert ".".join(map(str, VERSION_PARTS)) == VERSION
