## Proof of Training (PoT)

### Description

This repository contains a proof-of-concept implementation of the Proof of Training
(PoT) consensus mechanism-based blockchain network [PoT paper](todo). By improving upon
typical PoW-like consensus mechanisms, PoT enables the creation of a blockchain network
that offers two novel functionalities:

1. **Verifiable Machine Learning Training Delegation** - PoT allows for the delegation
   of arbitrary ML model training to a blockchain network, where each node independently
   performs training and verifies the correctness of the training process. This is
   especially useful in the case of a data injection attack, where a malicious party
   appends incorrectly labeled samples to the dataset. By incentivizing nodes to
   participate in the block mining process, PoT allows the detection of such attacks and
   the rejection of the training results. Performing injection attacks in PoT would be
   equivalent to performing a 51% attack on the blockchain network.

2. **Removing Wasteful PoW Computations** - PoW-based consensus mechanisms require nodes
   to perform wasteful computations to mine a block. There exist alternative consensus
   mechanisms (PoS, PoA, PoB, etc.) that do not require such computations, but people
   who have invested resources in acquiring computational power are not likely to
   abandon their investment and switch to more modern/eco-friendly consensus mechanisms.
   PoT aims to solve that problem by using computational infrastructure to perform a
   genuinely useful task—dedicated ML model training.

### About the code

PoT blockchain network nodes (employees) are simulated using OS processes
(`multiprocessing` library). Each node is a separate process that communicates with
other nodes using a `multiprocessing.Pipe` object what accurately represents P2P
communication in the network.

ML training is performed on simple DNN and MNIST dataset. Model is writen using `keras`
library. Each broadcasted protocol message correctness is checked by all other nodes as
specified in the paper.

Nodes log their actions to `pot_sim.log` file. Logs are in two levels of verbosity:

- `INFO` - information available to the network participants (e.g., broadcasted
  messages)
- `DEBUG` - information available only to the nodes themselves (e.g., individual
  training progress) `INFO` are also logged to the console.

### Getting started

To run the code, you need to have `Python >=3.8` installed on your machine.

#### Installing the requirements

To install the requirements using `pipenv` (recommended) in the project directory run:

```bash
pipenv install
```

or use your preferred package manager to install the requirements from the
`requirements.txt` file.

#### Running the simulation

To start the simulation run:

```bash
pipenv run python main.py
```

#### Simulation parameters

Values constant to the protocol simulation are defined in `simulation/constants.py` with
appropriate comments. Feel free to change them to see how the protocol behaves under
different conditions.

### Built with

- [Python](https://www.python.org/)
- [pipenv](https://pipenv.pypa.io/en/latest/)
- [pre-commit](https://pre-commit.com/)
