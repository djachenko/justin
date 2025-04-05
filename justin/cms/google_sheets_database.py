import webbrowser
from dataclasses import dataclass, fields, asdict
from functools import cache
from pathlib import Path
from typing import Type, List, Dict, Callable, TypeVar, Self

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from justin.shared.helpers.utils import fromdict, Json
from justin_utils.util import same

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class Link(str):
    pass


@dataclass
class GoogleSheetsEntry:
    @classmethod
    def sheet_name(cls) -> str:
        return cls.__name__

    @classmethod
    def header(cls) -> List[str]:
        # noinspection PyTypeChecker
        return [field.name for field in fields(cls)]

    @classmethod
    def from_dict(cls: Type[Self], json_object: Json, rules: Dict[Type, Callable] = None) -> Self:
        if rules is None:
            rules = {}

        return fromdict(json_object, cls, rules=rules | {
            bool: GoogleSheetsEntry.__parse_bool
        })

    def as_dict(self) -> Json:
        # noinspection PyTypeChecker
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


class GoogleSheetsDatabase:
    @dataclass
    class Sheet:
        id: int
        header: List[str] = None
        data: List[T] | None = None

    def __init__(self, spreadsheet_id: str, root: Path) -> None:
        super().__init__()

        self.__spreadsheet_id = spreadsheet_id
        self.__sheets: Dict[str, GoogleSheetsDatabase.Sheet] | None = None
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

    @property
    # @cache
    def __sheet_metadata(self) -> Dict:
        return self.__spreadsheets.get(spreadsheetId=self.__spreadsheet_id).execute()

    @property
    def __url(self) -> str:
        return self.__sheet_metadata["spreadsheetUrl"]

    def __refresh_sheets(self) -> None:
        sheets = self.__sheet_metadata["sheets"]

        self.__sheets = {
            sheet["properties"]["title"]: GoogleSheetsDatabase.Sheet(
                id=sheet["properties"]["sheetId"]
            ) for sheet in sheets
        }

    def __run_requests(self, *requests: GSRequest) -> None:
        self.__spreadsheets.batchUpdate(
            spreadsheetId=self.__spreadsheet_id,
            body={
                "requests": requests
            }
        ).execute()

        self.__clean_data()

    def __get_sheet(self, cls: Type[T]) -> Sheet:
        return self.__sheets[cls.sheet_name()]

    # region row data

    @staticmethod
    def __row_data(values):
        cell_datas = []

        for value in values:
            if value is None:
                continue
            elif isinstance(value, bool):
                value_dict = {
                    "boolValue": value,
                }
            elif isinstance(value, int) or isinstance(value, float):
                value_dict = {
                    "numberValue": value,
                }
            elif isinstance(value, Link):
                value_dict = {
                    "formulaValue": f"=HYPERLINK(\"{value}\")"
                }
            else:
                value_dict = {
                    "stringValue": str(value),
                }

            cell_datas.append({
                "userEnteredValue": value_dict,
            })

        return {
            "values": cell_datas,
        }

    # endregion

    # region requests

    def __append_row_request(self, cls: Type[T], row: GSRow) -> List[GSRequest]:
        sheet = self.__get_sheet(cls)

        return [{
            "appendCells": {
                "fields": "*",
                "rows": [
                    self.__row_data(row),
                ],
                "sheetId": sheet.id,
            }
        }]

    def __checkbox(self, cls: Type[T]) -> List[GSRequest]:
        sheet = self.__get_sheet(cls)

        requests = []

        for i, field in enumerate(fields(cls)):
            cell_data = None
            start = i
            end = i + 1

            if field.type == bool:
                cell_data = {
                    "dataValidation": {
                        "condition": {
                            "type": "BOOLEAN",
                        }
                    }
                }

            if cell_data:
                requests.append({
                    "repeatCell": {
                        "cell": cell_data,
                        "range": {
                            "sheetId": sheet.id,
                            "startRowIndex": 1,
                            "startColumnIndex": start,
                            "endColumnIndex": end,
                        },
                        "fields": "dataValidation",
                    }
                })

        return requests

    def __update_row_request(self, cls: Type[T], index: int, row: GSRow) -> List[GSRequest]:
        sheet = self.__get_sheet(cls)

        header_offset = 1

        return [{
            "updateCells": {
                "fields": "*",
                "rows": [
                    self.__row_data(row),
                ],
                "start": {
                    "sheetId": sheet.id,
                    "rowIndex": index + header_offset,  # header
                    "columnIndex": 0
                }
            }
        }]

    @staticmethod
    def __create_sheet_request(cls: Type[T]) -> List[GSRequest]:
        return [{
            "addSheet": {
                "properties": {
                    "title": cls.sheet_name(),
                    "gridProperties": {
                        "rowCount": 1,
                        "columnCount": len(fields(cls))
                    }
                }
            }
        }]

    def __write_header_request(self, cls: Type[T]) -> List[GSRequest]:
        return self.__update_row_request(
            cls,
            -1,
            cls.header()
        )

    def __delete_sheet_request(self, cls: Type[T]) -> List[GSRequest]:
        sheet = self.__get_sheet(cls)

        return [{
            "deleteSheet": {
                "sheetId": sheet.id
            }
        }]

    # endregion

    # region warmup

    def __warmup_spreadsheet(self) -> None:
        if self.__sheets is not None:
            return

        self.__refresh_sheets()

    def __warmup_sheet(self, cls: Type[T]) -> None:
        self.__warmup_spreadsheet()

        cls_name = cls.sheet_name()

        if cls_name not in self.__sheets:
            self.__run_requests(*self.__create_sheet_request(cls))

            self.__refresh_sheets()

            self.__run_requests(*self.__write_header_request(cls))

        sheet = self.__get_sheet(cls)

        if sheet.header is not None and sheet.data is not None:
            return

        result = self.__spreadsheets.values() \
            .get(
            spreadsheetId=self.__spreadsheet_id,
            range=f"{cls_name}"
        ) \
            .execute()

        header = result["values"][0]
        values = result["values"][1:]

        entities = []

        for row in values:
            padded_row = row + [""] * (6 - len(row))

            row_dict = dict(zip(header, padded_row))

            entity = cls.from_dict(row_dict)

            entities.append(entity)

        sheet.header = header
        sheet.data = entities

    def __clean_data(self) -> None:
        for sheet in self.__sheets.values():
            sheet.data = None

    # endregion

    def __prepare_row(self, entry: T) -> GSRow:
        cls = type(entry)

        self.__warmup_sheet(cls)
        sheet = self.__get_sheet(cls)

        entry_dict = entry.as_dict()

        entry_row = [entry_dict[h] for h in sheet.header]

        return entry_row

    # region entries operations

    def __append_entry(self, entry: T) -> List[GSRequest]:
        row = self.__prepare_row(entry)

        cls = type(entry)

        self.__get_sheet(cls).data.append(entry)

        return self.__append_row_request(cls, row)

    def __overwrite_entry(self, index: int, entry: T) -> List[GSRequest]:
        row = self.__prepare_row(entry)

        cls = type(entry)

        self.__get_sheet(cls).data[index] = entry

        return self.__update_row_request(cls, index, row)

    # endregion

    # region public contract

    def open(self, cls: Type[T] | None = None) -> None:
        url = self.__url

        if cls:
            url += f"?gid={self.__get_sheet(cls).id}"

        webbrowser.open(url)

    def get_entries(self, cls: Type[T]) -> List[T]:
        self.__warmup_sheet(cls)

        return self.__get_sheet(cls).data

    def update(self, *entries: T, comparator: Callable[[T, T], bool] = lambda a, b: a == b) -> None:
        if not entries:
            return

        requests = []

        assert same(type(entry) for entry in entries)
        cls = type(entries[0])

        for entry in entries:
            index_of_existing = None
            entries = self.get_entries(cls)

            for i, existing_entry in enumerate(entries):
                if comparator(existing_entry, entry):
                    index_of_existing = i

                    break

            if index_of_existing is not None:
                requests += self.__overwrite_entry(index_of_existing, entry)
            else:
                requests += self.__append_entry(entry)

        requests += self.__checkbox(cls)

        self.__run_requests(requests)

    def delete_sheet(self, cls: Type[T]) -> None:
        self.__run_requests(*self.__delete_sheet_request(cls))

    # endregion
