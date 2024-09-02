import logging

from network.network_utils import create_network
from simulation.constants import EMPLOYEES_NUM, USERS_NUM
from simulation.log_conig import init_logger
from simulation.simulation import Simulation


def main() -> None:
    """Main function of the proof of concept implementation of PoT blockchain
    network."""
    init_logger(
        console_log_level=logging.INFO, file_log_level=logging.INFO
    )  # create log file configuration
    broadcaster, employees, users_puppeteer, simulation_conn = create_network(
        employees_num=EMPLOYEES_NUM, users_num=USERS_NUM
    )  # create network parties (processes)
    simulation = Simulation(simulation_conn=simulation_conn)  # create simulation object
    simulation.set_parties(
        broadcaster=broadcaster, employees=employees, users_puppeteer=users_puppeteer
    )  # set parties used for the simulation
    simulation.run_simulation()  # run the simulation
    simulation.summarize_simulation()  # summarize results of the simulation


if __name__ == "__main__":
    main()
