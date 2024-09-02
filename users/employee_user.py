from network.transaction import Transaction
from users.user import User


class EmployeeUser(User):
    """Class for representing an employee user.

    A special type of user that is used as receiver of coinbase (block
    building) rewards.
    """

    def __init__(self, employee_name: str) -> None:
        super().__init__(name=employee_name)
        self.employee_name = employee_name

    def create_transaction(
        self, amount: float, receiver: User, employee_name: str = None
    ) -> Transaction:
        return super().create_transaction(
            amount=amount, receiver=receiver, employee_name=self.employee_name
        )
