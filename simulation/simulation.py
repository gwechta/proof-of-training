import logging
from multiprocessing import connection
from time import sleep
from typing import List, Any, Optional, TYPE_CHECKING

from network.broadcaster import Broadcaster
from network.users_puppeteer import UsersPuppeteer

logger = logging.getLogger()
if TYPE_CHECKING:
    from blockchain.blockchain import Blockchain


class Simulation:
    """A class handling simulation of blockchain network, used for storing the
    state of the simulation and for running the simulation itself.

    Simulation is a *singleton* class. It is required since some
    processes need to access the same instance of the simulation.
    """

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "Simulation":
        if cls._instance is None:
            cls._instance = super(Simulation, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, simulation_conn: Optional[connection.Connection] = None) -> None:
        if not self._initialized:
            self.simulation_conn = simulation_conn
            self.broadcaster: Optional[Broadcaster] = None
            self.employees: List[Any] = []
            self.users_puppeteer: Optional[UsersPuppeteer] = None
            self.result_local_blockchain: Optional[Blockchain] = None
            self._initialized: bool = True

    def run_simulation(self) -> None:
        self._initialize_employees_blockchains()
        self.broadcaster.start()  # broadcaster start as the first
        self.users_puppeteer.start()  # users_puppeteer start as the second
        for employee in self.employees:  # later all employees start
            employee.start()
        self.users_puppeteer.join()
        for employee in self.employees:
            employee.join()
        self.broadcaster.join()
        logger.info("\nAll processes have finished computing.\n")
        sleep(0.5)
        self.result_local_blockchain = (
            self.simulation_conn.recv().content
        )  # grab the result blockchain from the broadcaster-simulation Pipe end

    def get_employees_names(self) -> List[str]:
        """Get the names of all employees in the simulation.

        Returns:
            A list of names of all employees in the simulation.
        """
        return [employee.name for employee in self.employees]

    def set_parties(
        self,
        broadcaster: Broadcaster,
        employees: List[Any],
        users_puppeteer: UsersPuppeteer,
    ) -> None:
        """Set the parties involved in the simulation.

        Args:
            broadcaster: The broadcaster process.
            employees: A list of employees processes.
            users_puppeteer: The users_puppeteer process.
        """
        self.broadcaster = broadcaster
        self.employees = employees
        self.users_puppeteer = users_puppeteer

    def _initialize_employees_blockchains(self) -> None:
        for employee in self.employees:
            employee.blockchain.append_genesis_block()
        blockchains = []

        for employee in self.employees:
            blockchains.append(employee.blockchain)

    def summarize_simulation(self) -> None:
        logger.info("Summarizing simulation...")
        logger.info("Blockchain view:")
        logger.info(f"{self.result_local_blockchain}")
        logger.info("Transactional data.csv:")
        logger.info(
            f"Transactions: {len(self.result_local_blockchain.all_transactions)}"
        )
        logger.info(
            f"Coins transferred: "
            f"{self.result_local_blockchain.count_transferred_coins()}"
        )
