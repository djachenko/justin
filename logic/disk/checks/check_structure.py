import logger
import structure
from filesystem.folder import Folder
from structure import Structure


class CheckStructure:
    def check(self, entry: Folder, struct: Structure):
        subfolders = entry.subfolders()

        result = True

        if struct.has_implicit_sets:
            return True

        for subfolder in subfolders:
            if struct.has_substructure(subfolder.name):
                if not self.check(subfolder, struct[subfolder.name]):
                    result = False
            else:
                logger.error("Found unexpected subfolder {ctg} in folder {dst}".format(
                    ctg=subfolder.name, dst=entry.path))

                result = False

        if not struct.has_unlimited_files:
            for subfile in entry.subfiles():
                if not struct.has_file(subfile.name):
                    logger.error("Found unexpected subfile {ctg} in folder {dst}".format(
                        ctg=subfile.name, dst=entry.name))
    
                    result = False

        return result

    def check_structure(self) -> bool:
        print("Checking structure of disk {photoset_name}... ".format(photoset_name=self.name))

        possible_destinations = structure.disk_structure

        result = self.check(self.entry, possible_destinations)

        if result:
            print("passed")
        else:
            print("not passed")

        return result
