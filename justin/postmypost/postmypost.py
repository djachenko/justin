# Configure Bearer authorization: BearerAuth
import os
from typing import Iterable, List

import requests
from postmypost_rest_sdk import ApiClient, Configuration, PublicationsApi, Publication, ChannelsApi, Channel, \
    UploadInit, UploadApi, InitUploadRequest, InitUploadByFileRequest, UploadByFile

from justin.postmypost.channels import get_channels
from justin.postmypost.utils import get_all
from justin.shared.filesystem import File

configuration = Configuration(
    access_token=os.environ["BEARER_TOKEN"]
)


class Postmypost:
    def __init__(self):
        self.__client = ApiClient(Configuration(access_token=""))

        self.__channels = get_channels(self.__client)

    def get_channels(self) -> Iterable[Channel]:
        api = ChannelsApi(self.__client)

        channels = get_all(api.get_channels)

        return channels

    def get_publications(self, project_id: int) -> Iterable[Publication]:
        api = PublicationsApi(self.__client)

        publications = get_all(api.get_publications, project_id=project_id, sort="post_at")

        return publications

    def upload_files(self, project_id: int, files: List[File]) -> List[int]:
        api = UploadApi(self.__client)
        file_ids = []

        for file in files:
            request = InitUploadByFileRequest(
                project_id=project_id,
                name=file.name,
                size=file.size
            )

            upload_data: UploadByFile = api.init_upload(request)

            requests.post(
                upload_data.action,
                data=upload_data.fields,
                files={
                    "file": file.path.open("rb")
                }
            )

            api.complete_upload(upload_data.id)
            file_ids.append(upload_data.id)

        return file_ids

    def make_post
