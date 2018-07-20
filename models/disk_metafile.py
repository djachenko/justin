class Metafiling:
    def initialize(self) -> None:
        self.metafile = dict()
        self.write_metafile()

    def write_metafile(self) -> None:
        with open(structure.metafile_path(self.entry.path).to_string(), mode="w") as metafile:
            json.dump(self.metafile, metafile, indent=4)

    def read_metafile(self) -> dict:
        with open(structure.metafile_path(self.entry.path).to_string()) as metafile:
            metafile_contents = json.load(metafile)

            return metafile_contents

    # def fill_metafile(self):
    #     contents = []
    #
    #     destinations = self.read_destinations()
    #
    #     destinations = ["instagram"]
    #
    #     for destination in destinations:
    #         categories = self.read_categories(destination)
    #
    #         for category in categories:
    #             photosets = self.read_photosets(destination, category)
    #
    #             for photoset in photosets:
    #                 contents.append({
    #                     "category": category,
    #                     "destination": destination,
    #                     "name": photoset,
    #                 })
    #
    #     self.metafile["contents"] = contents