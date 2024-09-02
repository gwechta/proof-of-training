EMPLOYEES_NUM: int = 11  # number of blockchain network nodes in the simulation
USERS_NUM: int = 10  # number of transaction issuers in the simulation
MAX_TRANSACTIONS_NUM: int = 100  # how many transactions to generate during simulation
STAKEHOLDERS_NUM: int = 3  # the number of stakeholders in the network
# simulation will stop when this number of blocks is reached
TARGET_BLOCKCHAIN_LENGTH: int = 6
# how many training declarations are needed for generating a block header
EMPLOYER_CONFIDENCE: int = 3
TF_SEED: int = 42  # TensorFlow seed
TD_COINSTAKE: int = 2**252  # training declaration coinstake
BH_COINSTAKE: int = 2**251  # block header coinstake
ITERATIONS_PER_EPOCH = 6000  # arbitrary, results in batch_size of 10 for MNIST

assert (
    STAKEHOLDERS_NUM <= EMPLOYEES_NUM
), f"{STAKEHOLDERS_NUM=} cannot be greater than {EMPLOYEES_NUM=}."
