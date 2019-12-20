class DataSizeFormatter:
    class Unit:
        def __init__(self, size: int, acronym: str) -> None:
            super().__init__()

            self.size = size
            self.acronym = acronym

    __BYTE = Unit(1, "B")
    __KILOBYTE = Unit(__BYTE.size * 1024, "KB")
    __MEGABYTE = Unit(__KILOBYTE.size * 1024, "MB")
    __GIGABYTE = Unit(__MEGABYTE.size * 1024, "GB")

    @staticmethod
    def __determine_unit(size: int) -> Unit:
        sorted_units = sorted([
            DataSizeFormatter.__BYTE,
            DataSizeFormatter.__KILOBYTE,
            DataSizeFormatter.__MEGABYTE,
            DataSizeFormatter.__GIGABYTE,
        ],
            key=lambda u: u.size,
            reverse=True)

        for unit in sorted_units:
            if size > unit.size:
                return unit

        return DataSizeFormatter.__BYTE

    @staticmethod
    def from_bytes(size: int) -> str:
        unit = DataSizeFormatter.__determine_unit(size)

        converted_size = size / unit.size

        result = f"{converted_size:.2f} {unit.acronym}"

        return result
