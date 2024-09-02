import logging
from multiprocessing import Pipe, connection
from typing import List, Tuple

from employee.employee import Employee
from network.broadcaster import Broadcaster
from network.users_puppeteer import UsersPuppeteer

logger = logging.getLogger()


def create_network(
    employees_num: int, users_num: int
) -> Tuple[Broadcaster, List[Employee], UsersPuppeteer, connection.Connection]:
    """Create employees, users, and a broadcaster objects used later in the
    simulation.

    Args:
        employees_num: The number of employees to create.
        users_num: The number of users to create.

    Returns:
        Tuple[Broadcaster, List[Employee], UsersPuppeteer, connection.Connection]: A
        tuple containing the broadcaster, a list of employees, the users puppeteer,
        and the communication Pipe end for simulation.
    """
    broadcaster_employees_conns = []
    employees = []
    for _ in range(employees_num):
        broadcaster_conn, employee_con = Pipe()
        broadcaster_employees_conns.append(
            broadcaster_conn
        )  # create list of all Employee-Broadcaster Pipe ends for Broadcaster
        employee = Employee(connection_e=employee_con)
        employees.append(employee)

    broadcaster_users_puppeteer_conn, users_puppeteer_conn = Pipe()
    users_puppeteer = UsersPuppeteer(
        connection_up=users_puppeteer_conn, users_num=users_num
    )
    broadcaster_simulation_conn, simulation_conn = Pipe()
    broadcaster = Broadcaster(
        employees_conns=broadcaster_employees_conns,
        users_puppeteer_conn=broadcaster_users_puppeteer_conn,
        simulation_conn=broadcaster_simulation_conn,
    )
    return broadcaster, employees, users_puppeteer, simulation_conn
