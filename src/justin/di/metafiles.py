from justin.shared.metafiles.metafile import DriveMetafile, NoPostMetafile, LocationMetafile, AlbumMetafile, \
    PhotosetMetafile, PersonMetafile, GroupMetafile, PostMetafile, RootMetafile
from justin.shared.metafiles.migrations import MetafileMigrator, NegativeGroupIdMigration, NewStructureMigration
from justin.shared.metafiles.readwriters import MetafileReadWriterImpl


def setup_metafiles():
    metafile_types = [
        PostMetafile,
        GroupMetafile,
        PersonMetafile,
        PhotosetMetafile,
        AlbumMetafile,
        LocationMetafile,
        NoPostMetafile,
        DriveMetafile,
    ]

    migrator = MetafileMigrator(
        NegativeGroupIdMigration(),
        NewStructureMigration(*metafile_types),
    )

    readwriter = MetafileReadWriterImpl(migrator, *metafile_types)

    RootMetafile.set_reader(readwriter)
