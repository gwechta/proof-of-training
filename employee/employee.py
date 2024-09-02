import copy
import logging
import multiprocessing
import time
from datetime import datetime
from multiprocessing import connection
from typing import Type, Union, List, Optional

from blockchain.blockchain import Blockchain
from blockchain.blockchain_utils import pos_td_difficulty, pos_bh_difficulty
from employee.employee_utils import select_stage
from model.model import ExampleModel, ExampleDataset
from network.cryptographic_utils import (
    generate_key_pair,
    count_leading_zeros,
    verify_signature,
    sign_message,
    encode_to_bytes,
)
from network.message import Message, MessageType
from network.transaction import Transaction
from poa_messages.stakeholder_signature import StakeholderSignature
from poa_messages.stakeholder_signatures_book import StakeholderSignaturesBook
from poa_messages.wrapped_block import WrappedBlock
from pos_messages.block_header import BlockHeader
from pos_messages.pos_message import PoSMessage
from pos_messages.training_declaration import TrainingDeclaration
from pos_messages.training_declarations_book import TrainingDeclarationsBook
from simulation.constants import (
    STAKEHOLDERS_NUM,
    TD_COINSTAKE,
    BH_COINSTAKE,
    TARGET_BLOCKCHAIN_LENGTH,
    EMPLOYER_CONFIDENCE,
)
from users.employee_user import EmployeeUser

logger = logging.getLogger()


class Employee(multiprocessing.Process):
    """A class representing an Employee node in the PoT network.

    This class simulates the Employee's (or as called in the paper - node's)
    behaviour in the PoT network.
    It manifests the biggest part of the protocol logic. The methods and class itself
    was designed with focus on accurately depicting node's behaviour in the blockchain
    network.
    """

    def __init__(self, connection_e: connection.Connection):
        super().__init__(target=self.simulate)
        self.connection = connection_e  # Employee-Broadcaster Pipe end
        self.private_key, self.public_key = generate_key_pair()
        self.td_coinstake = (
            TD_COINSTAKE  # how many coins to stake for training declaration
        )
        self.bh_coinstake = BH_COINSTAKE  # how many coins to stake for block header
        self.blockchain = Blockchain(
            owner_name=self.name
        )  # local replica of blockchain
        self.model: Optional[ExampleModel] = None
        self.dataset: Optional[ExampleDataset] = None
        self.training_declaration: Optional[TrainingDeclaration] = None
        self.training_secret: Optional[bytes] = None
        self.block_header: Optional[BlockHeader] = None
        self.pending_transactions: List[Transaction] = []
        self.training_declarations_book = TrainingDeclarationsBook(owner_name=self.name)
        self.stakeholder_signatures_book = StakeholderSignaturesBook(
            owner_name=self.name
        )
        self.employee_user = EmployeeUser(
            employee_name=self.name
        )  # Employee's User object is used for hooking coinbase rewards to the Employee
        self.protocol_restart_flag = False  # flag used for restarting the protocol.

    def simulate(self) -> None:
        """Run the simulation for the employee.

        This method is target for employee process.
        The employee performs verifiable training and block building until the
        blockchain reaches the target length.

        Remark: This method exhibits redundant looking code for checking if the
        protocol should be restarted, it is done for the sake of clarity. Alternative
        approaches required complex function return points handling and were less
        readable. Since other employees are running in parallel, it may be a bit
        tricky to check when THIS employee should restart the protocol. The flag
        checks after each step of the protocol are used for that purpose.
        """
        # Start simulation
        self.connection.send(
            Message(msg_type=MessageType.EMPLOYEE_ALIVE)
        )  # message registers Employee in the Broadcaster
        logger.info(f"{self.name} is running.")
        model_ref, dataset_ref = select_stage()
        self._download_stage(model_ref=model_ref, dataset_ref=dataset_ref)
        # Begin protocol
        while self.blockchain.get_chain_length() < TARGET_BLOCKCHAIN_LENGTH:
            time.sleep(1)  # time for the network to settle
            self.protocol_restart_flag = False
            # Verifiable Training - Phase 1
            self._perform_training()  # during which `training_secret` is saved
            if self.protocol_restart_flag is True:
                continue
            self.training_declaration = self._create_training_declaration()
            if self.protocol_restart_flag is True:
                continue
            self._perform_pos_waiting_mechanism(
                pos_message=self.training_declaration
            )  # wait until PoS's timestamp check is true
            if self.protocol_restart_flag is True:
                continue
            if self.training_declaration.signature is None:
                logger.warning(self.training_declaration)
                raise TypeError
            self.connection.send(
                Message(
                    msg_type=MessageType.TRAINING_DECLARATION,
                    content=self.training_declaration,
                )
            )
            logger.info(
                f"{self.name} sent training_declaration["
                f"{self.training_declaration.get_id()}={self.training_declaration}]."
            )
            # Block Building - Phase 2
            if self.protocol_restart_flag is True:
                continue
            self._wait_for_training_declarations(id_s=self.training_declaration.id_s)
            if self.protocol_restart_flag is True:
                continue
            self.block_header = self._create_block_header()
            if self.protocol_restart_flag is True:
                continue
            self._perform_pos_waiting_mechanism(
                pos_message=self.block_header
            )  # Save block header
            if self.protocol_restart_flag is True:
                continue
            self.connection.send(
                Message(
                    msg_type=MessageType.BLOCK_HEADER,
                    content=self.block_header,
                )
            )
            logger.info(
                f"{self.name} sent block_header[{self.block_header.get_id()}="
                f"{self.block_header}]."
            )
            self._check_type_of_stakeholder(
                block_header=self.block_header, local_check=True
            )  # and save it
            if self.protocol_restart_flag is True:
                continue
            while self.protocol_restart_flag is False:
                self._collect_messages()
        # Finishing - Phase 3
        self.connection.send(
            Message(
                msg_type=MessageType.RESULT_LOCAL_BLOCKCHAIN,
                content=self.blockchain,
            )
        )
        logger.info(f"{self.name} sent local replica of blockchain.")
        self.connection.send(Message(msg_type=MessageType.EMPLOYEE_FINISHED))
        logger.info(f"{self.name} finished.")

    def _wait_for_training_declarations(self, id_s: str) -> None:
        """Wait until the number of training declarations for the given `id_s`
        is greater or equal to `EMPLOYER_CONFIDENCE`.

        Args:
            id_s: The training stage id.
        """
        while (
            self.training_declarations_book.get_training_declarations_num(id_s)
            < EMPLOYER_CONFIDENCE
        ):
            time.sleep(0.5)
            self._collect_messages()

    def _collect_messages(self) -> None:
        """Collect messages from the Broadcaster and processes them according
        to their type.

        The method runs until all pending messages are served.
        """
        while self.connection.poll() is True:
            recv_message: Message = self.connection.recv()
            match recv_message.msg_type:
                case MessageType.TRANSACTION:
                    t: Transaction = recv_message.content
                    self.pending_transactions.append(t)
                    logger.debug(f"{self.name} received {t}.")
                case MessageType.TRAINING_DECLARATION:
                    td: TrainingDeclaration = recv_message.content
                    logger.debug(
                        f"{self.name} received alien training_declaration["
                        f"{td.get_id()}]={td}."
                    )
                    if self._verify_alien_message_soundness(message=td) is True:
                        self.training_declarations_book.add_training_declaration_to_book(
                            td=td
                        )
                        logger.debug(
                            f"{self.name} accepted training_declaration["
                            f"{td.get_id()}]."
                        )
                    else:
                        logger.debug(
                            f"{self.name} rejected training_declaration[{td.get_id()}]."
                        )
                case MessageType.BLOCK_HEADER:
                    bh: BlockHeader = recv_message.content
                    logger.debug(
                        f"{self.name} received alien block_header[{bh.get_id()}]={bh}."
                    )
                    if self._verify_alien_message_soundness(message=bh) is True:
                        self._check_type_of_stakeholder(block_header=bh)
                        logger.debug(
                            f"{self.name} accepted block_header[{bh.get_id()}]."
                        )
                    else:
                        logger.debug(
                            f"{self.name} rejected block_header[{bh.get_id()}]."
                        )
                case MessageType.STAKEHOLDER_SIGNATURE:
                    ss: StakeholderSignature = recv_message.content
                    id_s, id_bh = ss.block_header.id_s, ss.block_header.get_id()
                    logger.debug(f"{self.name} received alien {ss}.")
                    is_roy = self._am_i_roy_stakeholder(block_header=ss.block_header)
                    self.stakeholder_signatures_book.add_signature_to_book(
                        ss=ss, roy=is_roy
                    )
                    if is_roy is True:
                        ss_for_roy_bh_num = (
                            self.stakeholder_signatures_book.get_signatures_num(
                                id_s=id_s,
                                id_bh=id_bh,
                            )
                        )
                        if ss_for_roy_bh_num >= STAKEHOLDERS_NUM - 1:
                            self._perform_roy_stakeholder_procedure(
                                block_header=ss.block_header
                            )
                case MessageType.WRAPPED_BLOCK:
                    wb: WrappedBlock = recv_message.content
                    logger.debug(f"{self.name} received alien {wb}.")
                    if (
                        wb.block_header.block_index
                        <= self.blockchain.get_latest_block().index
                    ):
                        logger.debug(
                            f"{self.name} discards {wb} "
                            f"because {wb.block_header.block_index} <= "
                            f"{self.blockchain.get_latest_block().index}."
                        )
                    else:
                        if self._verify_alien_message_soundness(message=wb):
                            # it means that Employee should exit waiting loop
                            self.protocol_restart_flag = True
                            self.stakeholder_signatures_book.close(id_s=wb.id_s)
                            logger.info(
                                f"{self.name} accepted wrapped_block[{wb.get_id()}]."
                            )
                            self.blockchain.append_fitted_wrapped_block(
                                wrapped_block=wb
                            )
                            self._remove_served_trans_from_pending_trans(
                                reg_trans=wb.transactions
                            )
                            logger.info(
                                f"{self.name} extended her blockchain to length "
                                f"{self.blockchain.get_chain_length()}."
                            )
                        else:
                            logger.debug(
                                f"{self.name} rejected wrapped_block[{wb.get_id()}]."
                            )
                case MessageType.EMPLOYEE_ALIVE:
                    logger.debug(f"{self.name} received generic {recv_message}.")
                case _:
                    raise TypeError(
                        f"Unsupported type of protocol message {recv_message}."
                    )

    def _am_i_roy_stakeholder(self, block_header: BlockHeader) -> bool:
        """Check if the employee is the Roy (K-th) stakeholder for the given
        `block_header`.

        Args:
            block_header: The block header for which the check is performed.

        Returns:
            bool: True if the employee is the Roy stakeholder, False otherwise.
        """
        stakeholders = self.blockchain.follow_the_coin(
            rand_source=block_header.calculate_hash()
        )
        return self.name == stakeholders[-1]

    def _check_type_of_stakeholder(
        self, block_header: BlockHeader, local_check: bool = False
    ) -> None:
        """Check if the employee is the NORMAL or ROY stakeholder for the given
        `block_header`.

        Args:
            block_header: The block header for which the check is performed.
            local_check: If True, the check is performed locally, without
                broadcasting stakeholder signature.
        """
        stakeholders = self.blockchain.follow_the_coin(
            rand_source=block_header.calculate_hash()
        )
        if self.name in stakeholders[:-1]:  # Normal stakeholder
            logger.info(
                f"{self.name} was NORMAL stakeholder for block_header["
                f"{block_header.get_id()}]{' locally checked' if local_check else ''}."
            )
            self._perform_normal_stakeholder_procedure(block_header=block_header)
        elif self.name == stakeholders[-1]:  # Roy stakeholder
            logger.info(
                f"{self.name} was ROY stakeholder for block_header["
                f"{block_header.get_id()}]{' locally checked' if local_check else ''}."
            )

    def _download_stage(
        self, model_ref: Type[ExampleModel], dataset_ref: Type[ExampleDataset]
    ) -> None:
        """Mock downloading model and dataset."""
        self.model = model_ref(owner_name=self.name)
        self.dataset = dataset_ref()

    def _perform_training(self) -> None:
        """Perform training and save the training secret."""
        self.training_secret = (
            self.model.train_one_batch_with_acquiring_training_secret(
                batch_size=self.dataset.batch_size,
                train_images=self.dataset.train_images,
                train_labels=self.dataset.train_labels,
            )
        )
        logger.info(f"{self.name} {self.training_secret=}")

    def _create_training_declaration(self) -> TrainingDeclaration:
        """Create training declaration message from values obtained so far.

        Returns:
            TrainingDeclaration: The training declaration message.
        """
        training_secret_commitment = sign_message(
            private_key=self.private_key, message=self.training_secret
        )
        training_declaration = TrainingDeclaration(
            model=self.model,
            training_secret_commitment=training_secret_commitment,
            public_key=self.public_key,
            coinstake=self.td_coinstake,
        )
        return training_declaration

    def _create_block_header(self) -> BlockHeader:
        """Create block header message from values obtained so far.

        Returns:
           BlockHeader: The block header message.
        """
        id_s = self.training_declaration.id_s
        training_declarations = (
            self.training_declarations_book.get_training_declarations(id_s=id_s)
        )  # add training declarations for `id_s` from the book
        block_header = BlockHeader(
            model=self.model,
            blockchain=self.blockchain,
            training_secret=self.training_secret,
            coinstake=self.bh_coinstake,
            public_key=self.public_key,
            training_declarations=training_declarations,
        )
        self.training_declarations_book.close(id_s=id_s)
        return block_header

    def _create_wrapped_block(self, block_header: BlockHeader) -> WrappedBlock:
        """Create wrapped block message from `block_header` and values obtained
        so far.

        Args:
            block_header: The block header message.

        Returns:
            WrappedBlock: The wrapped block message.
        """
        active_transactions = self._get_pending_transactions_and_set_employee()
        stakeholder_signatures = (
            self.stakeholder_signatures_book.get_signatures_for_block_header(
                id_s=self.model.get_id_s(), id_bh=block_header.get_id()
            )
        )
        wrapped_block = WrappedBlock(
            block_header=block_header,
            employee_user=self.employee_user,
            model=self.model,
            public_key=self.public_key,
            transactions=active_transactions,
            stakeholders_signatures=stakeholder_signatures,
        )
        return wrapped_block

    def _get_pending_transactions_and_set_employee(self) -> List[Transaction]:
        """Set the employee name for all pending transactions and return
        them."""
        active_transactions = copy.deepcopy(self.pending_transactions)
        for transaction in active_transactions:
            transaction.employee_name = self.name
        return active_transactions

    def _remove_served_trans_from_pending_trans(
        self, reg_trans: List[Transaction]
    ) -> None:
        """Remove served transactions from pending transactions."""
        served_trans_set = set(reg_trans)
        pending_trans_set = set(self.pending_transactions)
        result_trans_set = pending_trans_set - served_trans_set
        self.pending_transactions = list(result_trans_set)

    def _perform_pos_waiting_mechanism(self, pos_message: PoSMessage) -> None:
        """Wait until the PoS message meets its difficulty.

        Args:
            pos_message: The PoS message to wait for.
        """
        while True:
            begin_time = time.time()
            self._collect_messages()  # employee should check its connection for new
            # messages
            if self.protocol_restart_flag is True:
                break
            h_pos = pos_message.calculate_hash()
            match pos_message:
                case TrainingDeclaration():
                    logger.debug(
                        f"{self.name} checked training_declaration["
                        f"{pos_message.get_id()}] for "
                        f"{''.join(format(byte, '08b') for byte in h_pos)[:16]}..., "
                        f"with {count_leading_zeros(h_pos)=} >= "
                        f"{pos_td_difficulty(coinstake=self.td_coinstake)}."
                    )
                    if pos_message.check_meeting_pos_td_difficulty():
                        pos_message.sign(private_key=self.private_key)
                        self.training_declarations_book.add_training_declaration_to_book(
                            td=pos_message
                        )
                        return
                case BlockHeader():
                    logger.debug(
                        f"{self.name} checked block_header[{pos_message.get_id()}] for "
                        f"{''.join(format(byte, '08b') for byte in h_pos)[:16]}..., "
                        f"with {count_leading_zeros(h_pos)=} >= "
                        f"{pos_bh_difficulty(coinstake=self.bh_coinstake)}."
                    )
                    if pos_message.check_meeting_pos_bh_difficulty():
                        pos_message.sign(private_key=self.private_key)
                        self.block_header = pos_message
                        return
                case _:
                    raise TypeError("Unsupported type of PoS message.")

            pos_message.set_timestamp(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )  # update timestamp
            execution_time = time.time() - begin_time
            time.sleep(1.0 - execution_time)

    def _verify_alien_message_soundness(
        self, message: Union[TrainingDeclaration, BlockHeader, WrappedBlock]
    ) -> bool:
        """Verify the soundness (definition depends on the type of the message)
        of the alien message.

        Args:
            message: The alien message to verify.

        Returns:
            bool: True if the message is sound, False otherwise.
        """
        # verify signature
        try:
            if (
                verify_signature(
                    public_key=message.public_key,
                    message=message.dumps_without_sig(),
                    signature=message.signature,
                )
                is False
            ):
                logger.info(
                    f"{self.name} [{message.get_id()}] does not have a valid signature."
                )
                return False
        except TypeError:
            raise TypeError(f"{self.name} {message}[{message.get_id()}")
        match message:
            case TrainingDeclaration():
                # verify meeting difficulty
                if message.check_meeting_pos_td_difficulty() is False:
                    logger.info(
                        f"{self.name} training_declaration[{message.get_id()}] does "
                        f"not meet its PoS difficulty."
                    )
                    return False
            case BlockHeader():
                # verify meeting difficulty
                if message.check_meeting_pos_bh_difficulty() is False:
                    logger.info(
                        f"{self.name} block_header[{message.get_id()}] does not meet "
                        f"its PoS difficulty."
                    )
                    return False
                # verify soundness of included training declarations
                if message.check_included_training_declarations() is False:
                    logger.info(
                        f"{self.name} block_header[{message.get_id()}] contains "
                        f"incorrect training_secret_commitments."
                    )
                    return False
            case WrappedBlock():
                # verify stakeholder signatures
                if message.verify_stakeholder_signatures() is False:
                    logger.info(
                        f"{self.name} wrapped_block[{message.get_id()}] contains "
                        f"incorrect stakeholder signatures."
                    )
                    return False
            case _:
                raise TypeError("Unsupported type of PoS message.")

        return True

    def _perform_normal_stakeholder_procedure(self, block_header: BlockHeader) -> None:
        """Perform Normal stakeholder procedure for the given `block_header`.

        Args:
            block_header: The block header for which the procedure is performed.
        """
        signature = sign_message(
            private_key=self.private_key, message=block_header.dumps_without_sig()
        )
        stakeholder_signature = StakeholderSignature(
            block_header=block_header,
            public_key=encode_to_bytes(self.public_key),
            signature=signature,
        )
        is_roy = self._am_i_roy_stakeholder(
            block_header=stakeholder_signature.block_header
        )
        self.stakeholder_signatures_book.add_signature_to_book(
            ss=stakeholder_signature, roy=is_roy
        )
        self.connection.send(
            Message(
                msg_type=MessageType.STAKEHOLDER_SIGNATURE,
                content=stakeholder_signature,
            )
        )
        logger.info(f"{self.name} sent {stakeholder_signature}.")

    def _perform_roy_stakeholder_procedure(self, block_header: BlockHeader) -> None:
        """Perform Roy stakeholder procedure for the given `block_header`.

        Args:
            block_header: The block header for which the procedure is performed.
        """
        wrapped_block = self._create_wrapped_block(block_header=block_header)
        wrapped_block.sign(private_key=self.private_key)
        self.connection.send(
            Message(msg_type=MessageType.WRAPPED_BLOCK, content=wrapped_block)
        )
        logger.info(
            f"{self.name} sent wrapped_block[{wrapped_block.get_id()}={wrapped_block}]."
        )
        self.blockchain.append_fitted_wrapped_block(wrapped_block=wrapped_block)
        logger.info(
            f"{self.name} extended her blockchain to length "
            f"{self.blockchain.get_chain_length()}."
        )
        self._remove_served_trans_from_pending_trans(
            reg_trans=wrapped_block.transactions
        )
        self.protocol_restart_flag = True
