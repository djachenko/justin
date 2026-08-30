from typing import List

from postmypost_rest_sdk import ChannelsApi, Channel, ApiClient

from justin.postmypost.utils import get_all


def get_channels(client: ApiClient) -> List[Channel]:
    api = ChannelsApi(client)

    channels: List[Channel] = list(get_all(api.get_channels()))

    return channels
