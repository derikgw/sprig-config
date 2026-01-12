from sprigconfig import (
    config_inject,
    ConfigValue
)

class MSSQLDatabase:

    def __init__(
        self,
        url: str,
        port: int,
        database: str
    ):
        self.url = url
        self.port = port
        self.database = database

    @config_inject
    def connect(
        self,
        user: str = ConfigValue("mssql_database.server.user"),
        password: str = ConfigValue("mssql_database.server.password")
    ):
        print(f"This is {self.__class__.__name__} invoked with User: {user} and Password: {password}")

