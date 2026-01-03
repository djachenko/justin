from typing import List

import face_recognition

from justin.actions.destinations_aware_action import DestinationsAwareAction
from justin.actions.pattern_action import Extra
from justin.shared.context import Context
from justin.shared.filesystem import Folder, File

Face = List


class FindFacesAction(DestinationsAwareAction):
    def __init__(self):
        self.__encodings = {}

    def handle_my_people(self, my_people_folder: Folder, context: Context, extra: Extra) -> None:
        samples_path = context.people_portraits

        if not samples_path.exists():
            print(f"Samples path does not exist: {samples_path}")
            return

        print(f"Loading known faces from {samples_path}")
        self.__encodings = (self.__encodings or
                            {file.stem: self.__load_single_face(file) for file in context.people_portraits.files})

        print(f"Processing {len(my_people_folder.files)} files in my_people folder")

        for file in my_people_folder.files:
            people = list(set(self.__find_people(file)))

            print(people)

            if not people:
                people = ["no_face"]

            for person in people:
                self.__copy_to_person_folder(file, person, my_people_folder)

    def handle_common(self, folder: Folder, context: Context, extra: Extra) -> None:
        pass

    def __load_single_face(self, file: File) -> Face:
        faces = self.__load_faces(file)

        assert len(faces) == 1

        return faces[0]

    def __load_faces(self, file: File) -> List[Face]:
        image = face_recognition.load_image_file(str(file.path))
        encodings = face_recognition.face_encodings(image)

        return encodings

    def __find_people(self, file: File) -> List[str]:
        """Обрабатывает один файл изображения"""
        print(f"Processing {file.name}")

        found_faces = self.__load_faces(file)
        people = []

        for face in found_faces:
            recognized_person = self.__find_matching_person(face)

            if not recognized_person:
                free_name = self.__find_free_unknown_name()

                self.__encodings[free_name] = face
                recognized_person = free_name

            people.append(recognized_person)

        return people

    def __find_matching_person(self, face_encoding: Face) -> str | None:
        """Находит совпадение с известными лицами"""
        for person_name, person_face in self.__encodings.items():
            print(person_name)

            matches = face_recognition.compare_faces([person_face], face_encoding, tolerance=0.6)

            if any(matches):
                return person_name

        return None

    def __find_free_unknown_name(self) -> str:
        """Находит свободное имя для новой группы неизвестных лиц"""
        counter = 1
        while True:
            name = f"unknown_{counter}"

            # Проверяем, что имя не занято в self.__encodings
            if name not in self.__encodings:
                return name

            counter += 1

    def __copy_to_person_folder(self, file: File, person_name: str, my_people_folder: Folder) -> None:
        """Копирует файл в папку соответствующего человека"""
        person_folder_path = my_people_folder.path / person_name
        person_folder_path.mkdir(exist_ok=True)

        file.copy(person_folder_path)
