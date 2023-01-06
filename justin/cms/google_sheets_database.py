from dataclasses import dataclass, fields
from functools import lru_cache
from pathlib import Path
from typing import Type, List, Dict, Callable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from justin.cms.db import Database, T

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

Row = List[str]


class GoogleSheetsDatabase(Database):
    @dataclass
    class Sheet:
        id: int
        header: List[str] = None
        data: List[T] = None

    def __init__(self, spreadsheet_id: str, root: Path) -> None:
        super().__init__()

        self.__spreadsheet_id = spreadsheet_id
        self.__sheets: Dict[str, GoogleSheetsDatabase.Sheet] | None = None
        self.__root = root

    @property
    @lru_cache()
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

    def __refresh_sheets(self):
        sheet_metadata = self.__spreadsheets.get(spreadsheetId=self.__spreadsheet_id).execute()
        sheets = sheet_metadata["sheets"]

        self.__sheets = {sheet["properties"]["title"]: GoogleSheetsDatabase.Sheet(
            id=sheet["properties"]["sheetId"]
        ) for sheet in sheets}

    def __run_requests(self, *requests):
        self.__spreadsheets.batchUpdate(spreadsheetId=self.__spreadsheet_id, body={
            "requests": requests
        }).execute()

    @staticmethod
    def __row_data(values):
        return {
            "values": [{
                "userEnteredValue": {
                    "stringValue": str(value)
                }
            } for value in values if value is not None]
        }

    def update_row_request(self, type_: Type[T], index: int, row: List):
        sheet = self.__sheets[type_.type()]

        header_offset = 1

        return [{
            "updateCells": {
                "fields": "*",
                "rows": [self.__row_data(row), ],
                "start": {
                    "sheetId": sheet.id,
                    "rowIndex": index + header_offset,  # header
                    "columnIndex": 0
                }
            }
        }]

    def append_row_request(self, type_: Type[T], row: List):
        sheet = self.__sheets[type_.type()]

        return [{
            "appendCells": {
                "fields": "*",
                "rows": [self.__row_data(row), ],
                "sheetId": sheet.id,
            }
        }]

    @staticmethod
    def __create_sheet_request(type_: Type[T]):
        return [{
            "addSheet": {
                "properties": {
                    "title": type_.type(),
                    "gridProperties": {
                        "rowCount": 1,
                        "columnCount": len(fields(type_))
                    }
                }
            }
        }]

    def __write_header(self, type_: Type[T]):
        return self.update_row_request(type_, -1, [field.name for field in fields(type_)])

    def __warmup_spreadsheet(self):
        if self.__sheets is not None:
            return

        self.__refresh_sheets()

    def __warmup_sheet(self, type_: Type[T]):
        self.__warmup_spreadsheet()

        type_name = type_.type()

        if type_name not in self.__sheets:
            self.__run_requests(*self.__create_sheet_request(type_))

            self.__refresh_sheets()

            self.__run_requests(*self.__write_header(type_))

        sheet = self.__sheets[type_name]

        if sheet.header is not None and sheet.data is not None:
            return

        result = self.__spreadsheets.values() \
            .get(
            spreadsheetId=self.__spreadsheet_id,
            range=f"{type_name}"
        ) \
            .execute()

        header = result["values"][0]
        values = result["values"][1:]

        entities = []

        for row in values:
            padded_row = row + [""] * (6 - len(row))

            row_dict = dict(zip(header, padded_row))

            entity = type_.from_dict(row_dict)

            entities.append(entity)

        sheet.header = header
        sheet.data = entities

    def get(self, type_: Type[T]) -> List[T]:
        self.__warmup_sheet(type_)

        return self.__sheets[type_.type()].data

    def __prepare_row(self, entry):
        self.__warmup_sheet(type(entry))

        entry_dict = entry.as_dict()

        entry_row = [entry_dict[h] for h in self.__sheets[type(entry).type()].header]

        return entry_row

    def __append_entry(self, entry: T):
        entry_row = self.__prepare_row(entry)

        type_ = type(entry)

        self.__sheets[type_.type()].data.append(entry)

        return self.append_row_request(type_, entry_row)

    def __overwrite_entry(self, index: int, entry: T):
        entry_row = self.__prepare_row(entry)

        type_ = type(entry)

        self.__sheets[type_.type()].data[index] = entry

        return self.update_row_request(type_, index, entry_row)

    def update(self, *entries: T, comparator: Callable[[T, T], bool] = lambda a, b: a == b) -> None:
        requests = []

        for entry in entries:
            index_of_existing = None
            entries = self.get(type(entry))

            for i, existing_entry in enumerate(entries):
                if comparator(existing_entry, entry):
                    index_of_existing = i

                    break

            if index_of_existing is not None:
                requests += self.__overwrite_entry(index_of_existing, entry)
            else:
                requests += self.__append_entry(entry)

        self.__run_requests(requests)


def get_service(token_path):
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path.as_posix(), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('../../.justin/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with token_path.open("w") as token:
            token.write(creds.to_json())

    service = build("sheets", "v4", credentials=creds)

    return service
