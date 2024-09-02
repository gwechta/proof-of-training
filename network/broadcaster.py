import logging
from multiprocessing import Process, connection
from typing import List, Optional, Any

from network.message import MessageType, Message
from simulation.constants import EMPLOYEES_NUM

logger = logging.getLogger()


class Broadcaster(Process):
    """This class represents a broadcaster process facilitating Employee-
    Employee and Employees-Simulation message exchange.

    In the context of blockchain networks, the Broadcaster is an
    artificial party used for simplifying communication between
    processes.
    """

    def __init__(
        self,
        employees_conns: List[connection.Connection],
        users_puppeteer_conn: connection.Connection,
        simulation_conn: connection.Connection,
    ):
        super().__init__(target=self.simulate)
        self.employees_connections = employees_conns
        self.users_puppeteer_conn = users_puppeteer_conn
        self.simulation_conn = simulation_conn
        self.should_stop = False
        self.finished_employees_num = 0
        self.result_local_blockchain_sent = False

    def simulate(self) -> None:
        """Simulate the behavior of the broadcaster by running an infinite loop
        that listens for incoming messages and broadcasts them to all connected
        nodes.

        The method logs when it starts and finishes.
        """
        logger.info(f"{self.name} is running.")
        self.stay_tuned_for_messages()
        logger.info(f"{self.name} finished.")
        return None

    def stay_tuned_for_messages(self) -> None:
        """Listen for incoming messages from employees and users puppeteer and
        broadcast them to all employees except the sending one.

        The behavior has two exceptions:
        - employee sends EMPLOYEE_FINISHED - broadcaster registers it and logs the
        event. Used for detecting when all employees finished.
        - employee sends RESULT_LOCAL_BLOCKCHAIN - broadcaster sends it to the
        simulation process. Used for displaying the state of blockchain after the
        simulation finishes.
        """
        while self.should_stop is False:
            for recv_conn_id, recv_connection in enumerate(self.employees_connections):
                if recv_connection.poll() is True:
                    recv_message: Message = recv_connection.recv()
                    match recv_message.msg_type:
                        case MessageType.EMPLOYEE_FINISHED:
                            self._register_finished_employee()
                            logger.info(
                                f"{self.name} registered "
                                f"{self.finished_employees_num} finished employees."
                            )
                        case MessageType.RESULT_LOCAL_BLOCKCHAIN:
                            if self.result_local_blockchain_sent is False:
                                self.simulation_conn.send(recv_message)
                                self.result_local_blockchain_sent = True
                        case _:
                            self._broadcast_message(
                                message=recv_message, excluded_list=[recv_conn_id]
                            )
            if self.users_puppeteer_conn.poll() is True:
                recv_message_up: Message = self.users_puppeteer_conn.recv()
                self._broadcast_message(message=recv_message_up)

    def _broadcast_message(
        self, message: Any, excluded_list: Optional[List[int]] = None
    ) -> None:
        """Broadcast a message to all employees except the ones in the excluded
        list.

        Args:
            message: The message to be broadcasted.
            excluded_list: A list of employee ids to be excluded from the broadcast.
            Defaults to None.
        """
        if excluded_list is None:
            excluded_list = []
        for send_conn_id, send_connection in enumerate(self.employees_connections):
            if send_conn_id not in excluded_list:
                send_connection.send(message)

    def _register_finished_employee(self) -> None:
        self.finished_employees_num += 1
        if self.finished_employees_num >= EMPLOYEES_NUM:
            self.should_stop = True
