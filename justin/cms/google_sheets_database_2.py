import webbrowser
from collections import defaultdict
from dataclasses import dataclass, fields, asdict
from functools import cache
from pathlib import Path
from typing import Type, List, Dict, Callable, TypeVar, Self

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from justin.shared.helpers.utils import fromdict, Json
from justin_utils.util import same, keydefaultdict

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

@dataclass
class GoogleSheetsEntry:
    @classmethod
    def sheet_name(cls) -> str:
        return cls.__name__

    @classmethod
    def header(cls) -> List[str]:
        return [field.name for field in fields(cls)]

    @classmethod
    def from_dict(cls: Type[Self], json_object: Json, rules: Dict[Type, Callable] = None) -> Self:
        if rules is None:
            rules = {}

        return fromdict(json_object, cls, rules=rules | {
            bool: GoogleSheetsEntry.__parse_bool
        })

    def as_dict(self) -> Json:
        return asdict(self)

    @staticmethod
    def __parse_bool(json) -> bool | None:
        if json == "FALSE":
            return False

        if json == "TRUE":
            return True

        return None


DATETIME_FORMAT = "%H:%M:%S %d.%m.%Y"

GSRequest = Dict[str, Dict]
GSRow = List

T = TypeVar("T", bound=GoogleSheetsEntry)

class Service:
    def __init__(self, root: Path) -> None:
        super().__init__()

        self.__root = root

    @property
    @cache
    def __spreadsheets(self):
        token_path = self.__root / "token.json"
        creds = None

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(token_path.as_posix(), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file((self.__root / "credentials.json").as_posix(), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with token_path.open("w") as token:
                token.write(creds.to_json())

        service = build("sheets", "v4", credentials=creds)

        return service.spreadsheets()

    def run_requests(self, spreadsheet_id: str, *requests: GSRequest) -> None:
        self.__spreadsheets.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": requests
            }
        ).execute()

    def values(self, spreadsheet_id: str, sheet_name: str):
        return self.__spreadsheets.values() \
            .get(
            spreadsheetId=spreadsheet_id,
            range=sheet_name
        ) \
            .execute()["values"]

    def spreadsheet_metadata(self, spreadsheet_id: str):
        return self.__spreadsheets.get(spreadsheetId=spreadsheet_id).execute()


class Sheet:
    # id: int
    # header: List[str] = None

    def __init__(self, name: str, service: Service) -> None:
        super().__init__()

        self.__name = ""
        self.__spreadsheet_id = ""
        self.__service = service

    def data(self) -> List[T]:
        result = self.__service.values(
            spreadsheet_id=self.__spreadsheet_id,
            sheet_name=self.__name
        )

        header = result[0]
        data = result[1:]

        return data


class Spreadsheet:
    def __init__(self, spreadsheet_id: str, service: Service):
        super().__init__()

        self.__id = spreadsheet_id
        self.__service = service

        self.__sheets = keydefaultdict(self.__create_sheet)

    @property
    def __metadata(self):
        return self.__service.spreadsheet_metadata(self.__id)

    @property
    def __url(self) -> str:
        return self.__metadata["spreadsheetUrl"]

    def __create_sheet(self, cls: Type[T]) -> Sheet:
        return Sheet(cls.sheet_name(), self.__service)

    def open(self, cls: Type[T] | None = None) -> None:
        url = self.__url

        if cls:
            url += f"?gid={self.__sheets[cls].id}"

        webbrowser.open(url)

    def get_entries(self, cls: Type[T]) -> List[T]:
        pass

    def update(self, *entries: T, comparator: Callable[[T, T], bool] = lambda a, b: a == b) -> None:
        pass

    def delete_sheet(self, cls: Type[T]) -> None:
        self.__service.run_requests(
            self.__id,

        )
