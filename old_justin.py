# import structure
# from filesystem import fs
# from models.photoset import Photoset
#
#
# def init() -> list:
#     disks = fs.find_disks()
#     results = []
#
#     for disk in disks:
#         photo_path = structure.photos_path(disk)
#
#         possible_destinations = structure.destinations()
#
#         destinations_on_disk = [destination for destination in possible_destinations if fs.path_exists(
#             fs.build_path(photo_path, destination))]
#
#         for destination in destinations_on_disk:
#             possible_categories = structure.categories(destination)
#
#             categories_on_disk = [category for category in possible_categories if fs.path_exists(
#                 fs.build_path(photo_path, destination, category))]
#
#             for category in categories_on_disk:
#                 subfolders = fs.subfolders(fs.build_path(photo_path, destination, category))
#
#                 photosets = [Photoset(subfolder.name, subfolder) for subfolder in subfolders]
#
#                 for photoset in photosets:
#                     print(photoset)
#
#                     results.append(photoset)
#
#                 a = 7
#
#     a = 7
#
#     return results
