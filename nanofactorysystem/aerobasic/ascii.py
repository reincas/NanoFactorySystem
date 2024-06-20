import socket
import time
from typing import Optional

from nanofactorysystem.aerobasic import AeroBasicAPI, SingleAxis
from nanofactorysystem.aerobasic.constants import ReturnCode, Version, DataItemEnum
from nanofactorysystem.utils.typing import StatusQueryType


class AerotechError(Exception):
    pass


class AsciiCommandResponse:
    def __init__(self, command: str):
        self.command = command

        # Return data
        self.return_code: Optional[ReturnCode] = None
        self.data: Optional[str] = None
        self.error: Optional[str] = None

        # Timings
        self.timestamp_sent: Optional[float] = None
        self.timestamp_received: Optional[float] = None
        self.timestamp_error: Optional[float] = None

    def __str__(self) -> str:
        """
        Formats the AsciiCommandResponse. Examples:
            - [SUCCESS] 'ENABLE X' -> '' <1716309894.6362026 -> 1716309894.6562026 ping=20ms>
            - [INVALID] 'ENBALE X' -> ''<1716309894.6362026 -> 1716309894.6562026 ping=20ms>
            - [FAULT] 'ENABLE X' -> '' (Axis already enabled!) <1716309894.6362026 -> 1716309894.6562026 ping=20ms>
            - [WAIT] 'ENABLE X' -> <1716309894.6362026>
            - [PENDING] 'ENABLE X'
        """
        if self.has_response():
            if self.has_error():
                error_string = f" ({self.error})"
            else:
                error_string = ""

            return (
                f"[{self.return_code.name}] {repr(self.command)} -> {repr(self.data)}{error_string} "
                f"<{self.timestamp_sent} -> {self.timestamp_received} ping={self.ping * 1000}ms>"
            )
        if self.is_sent():
            return f"[WAIT] {repr(self.command)} -> <{self.timestamp_sent}>"
        return f"[PENDING] {repr(self.command)}"

    def is_sent(self) -> bool:
        return self.timestamp_sent is not None

    def has_response(self) -> bool:
        return self.return_code is not None

    def has_error(self) -> bool:
        return self.error is not None

    @property
    def ping(self) -> float:
        if self.timestamp_sent is None:
            return -float("inf")

        if self.timestamp_received is None:
            return float("inf")

        return self.timestamp_received - self.timestamp_sent


class AerotechAsciiInterface(AeroBasicAPI):
    COMMAND_TERMINATING_CHARACTER = 10  # \n

    def __init__(self, hostname: str = "127.0.0.1", port: int = 8000):
        super().__init__()
        self.hostname = hostname
        self.port = port
        self.history: list[AsciiCommandResponse] = []

        # TCP socket to the A3200 system
        self.socket: Optional[socket.socket] = None
        self._follow_errors = True  # Internal variable that is used to avoid recursion

    def __call__(self, program):
        from nanofactorysystem.aerobasic.programs import AeroBasicProgram
        if isinstance(program, str):
            for line in program.split("\n"):
                self.send(line)
        elif isinstance(program, AeroBasicProgram):
            for line in program.lines:
                self.send(line)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(hostname={self.hostname}, port={self.port})"

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False  # Propagate exception to higher levels

    def __del__(self):
        self.close()

    def __enter__(self):
        return self.connect()

    @property
    def is_opened(self) -> bool:
        return self.socket is not None

    def connect(self) -> "AerotechAsciiInterface":
        if self.socket is None:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.hostname, self.port))
            except ConnectionRefusedError:
                self.logger.error(f"Connection to A3200 controller failed! ({self.hostname}:{self.port})")
                raise
        return self

    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def send(self, command: str) -> str:
        """ Run the given AeroBasic command on the A3200 controller. """

        if not self.is_opened:
            raise RuntimeError("Not connected!")

        # Append terminal character
        if not command.endswith(chr(self.COMMAND_TERMINATING_CHARACTER)):
            command += chr(self.COMMAND_TERMINATING_CHARACTER)

        # Send command
        cmd_resp = AsciiCommandResponse(command)
        self.history.append(cmd_resp)
        cmd_resp.timestamp_sent = time.time()
        self.socket.send(command.encode())

        # Read and return response
        code, *data = self.socket.recv(4096).decode().strip()
        cmd_resp.timestamp_received = time.time()
        data = "".join(data)
        cmd_resp.return_code = ReturnCode(ord(code))
        cmd_resp.data = data

        # Check return code
        self.logger.debug(str(cmd_resp))
        if cmd_resp.return_code == ReturnCode.SUCCESS:
            return data

        # Error handling -> Invalid Syntax
        if cmd_resp.return_code == ReturnCode.INVALID:
            raise AerotechError(f"Command '{command.strip()}' has an invalid syntax!")

        # Error handling -> Code execution failed
        if cmd_resp.return_code == ReturnCode.FAULT:
            if self._follow_errors:
                error = self.LAST_ERROR()
            else:
                error = "Error retrieving last error..."

            cmd_resp.error = error
            self.logger.error(str(cmd_resp))

            raise AerotechError(f"Execution failed for {command}. Reason: {error}")

        raise RuntimeError(f"Could not identify return code {code}")

    # SYSTEM COMMANDS
    def LAST_ERROR(self) -> str:
        self._follow_errors = False
        resp = self.send("~LASTERROR")
        self._follow_errors = True
        return resp

    def VERSION(self) -> Version:
        """
        Use the ~VERSION command to retrieve the version of the A3200 software that is running on the server.
        The ASCII command interface returns version information in the format of MAJOR.MINOR.REVISION.BUILD.
        """
        return Version.parse_string(self.send("~VERSION"))

    def RESETCONTROLLER(self) -> str:
        """
        Use the ~RESETCONTROLLER command to reset the controller. This command has the same functionality as when
        you click the Reset Controller button in Motion Composer. The ASCII command interface does not respond to
        this command until the reset completes.
        """
        return self.send("~RESETCONTROLLER")

    def TASK(self, task_id: int) -> str:
        """
        Use the ~TASK command to change the task on which controller commands execute. By default, controller
        commands execute on the Library task. If you change the executing task, the executing task changes only for
        that specific client. The executing tasks of other clients do not change.

        If the value that you specify for the <TaskID> argument is negative, or if the value is greater than
        the number of possible tasks, the ASCII command interface returns the CommandInvalidCharacter. If you specify
        a valid value for the <TaskID> argument and the specified task cannot execute commands, for example the task
        is in the PLCReserved state, the interface returns the CommandFaultCharacter.
        """
        return self.send(f"~TASK {task_id}")

    def STOPTASK(self, task_id: Optional[int]) -> str:
        """
        Use the ~STOPTASK command to stop a task and reset all the states for that task.
        This command has the same functionality as when you click the Stop button in Motion Composer.
        The <TaskID> argument is optional. If you specify the <TaskID> argument, the ~STOPTASK command stops the
        specified task. If you do not specify the <TaskID> argument, this command stops the current task of the client.
        """
        if task_id is None:
            return self.send("~STOPTASK")
        return self.send(f"~STOPTASK {task_id}")

    def STATUS(self, *query_tuples: StatusQueryType):
        def stringify_query(query):
            """ Converts all arguments to strings if necessary """
            args = []
            for item in query:
                if isinstance(item, str):
                    args.append(item)
                elif isinstance(item, DataItemEnum):
                    args.append(str(item.name))  # Need value here and not DataItem_value!
                elif isinstance(item, SingleAxis):
                    args.append(item.parameter_name)
                else:
                    args.append(str(item))

            return args

        query_string = " ".join([
            f"({', '.join(stringify_query(query))})"
            for query in query_tuples
        ])
        return self.send(f"~STATUS {query_string}")


class DummyAsciiInterface(AerotechAsciiInterface):
    def send(self, command: str) -> str:
        self.logger.debug(command)
        return command

    def connect(self) -> "AerotechAsciiInterface":
        return self

    def close(self):
        pass
