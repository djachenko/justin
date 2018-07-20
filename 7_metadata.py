import util


def check_metadata_existence(path):
    entries = os.scandir(path)

    nef_names = util.names_by_extension(entries, "nef")
    xmp_names = util.names_by_extension(entries, "xmp")

    return len(set(nef_names).difference(xmp_names)) > 0


def check_metadata_actuality(path):
    return True


def check_metadata(path):
    return check_metadata_existence(path) and check_metadata_actuality(path)