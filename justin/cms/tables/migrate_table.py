from justin.cms.tables.table import Table


def migrate_table(src: Table, dst: Table) -> None:
    src.load()
    dst.load()

    assert not dst.entries

    dst.entries = src.entries

    dst.save()

