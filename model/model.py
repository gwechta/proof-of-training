import hashlib
import logging
import struct
from typing import Any

import tensorflow as tf
from tensorflow.keras.datasets import mnist
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.models import Sequential

from simulation.constants import TF_SEED

tf.random.set_seed(TF_SEED)
tf.keras.utils.set_random_seed(TF_SEED)

logger = logging.getLogger()


class ExampleDataset:
    """A class representing the MNIST dataset used as an example in the PoT
    proof of concept implementation."""

    def __init__(self) -> None:
        (train_images, train_labels), (
            test_images,
            test_labels,
        ) = mnist.load_data()  # Load the MNIST dataset
        self.train_images = train_images / 255.0
        self.train_labels = train_labels
        self.test_images = test_images / 255.0
        self.test_labels = test_labels
        self.iterations_per_epoch = 6000  # arbitrary, results in batch_size of 10
        self.batch_size = len(train_images) // self.iterations_per_epoch


class ExampleModel:
    """A simple deep neural network model for MNIST classification used as an
    example in the PoT proof of concept implementation."""

    def __init__(self, owner_name: str) -> None:
        self.id = "Simple DNN for MNIST classification"
        self.owner_name = owner_name
        self.num_of_epochs = 1
        self.current_iteration = -1
        self.model = Sequential(
            [  # Define the neural network model and compile it
                Flatten(input_shape=(28, 28)),  # Flatten the 28x28 input images
                Dense(128, activation="relu"),  # 128 units with ReLU activation
                Dense(
                    10, activation="softmax"
                ),  # 10 units, 10 classes with softmax activation
            ]
        )
        self.model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

    def train_one_batch_with_acquiring_training_secret(
        self, batch_size: int, train_images: Any, train_labels: Any
    ) -> bytes:
        """Train the model on one batch of the training data.csv and acquire
        the training secret.

        For details on training generation see the paper.
        Noticeably in practical implementations, train_on_batch() should be replaced
        by a specific to given ML framework train_on_sample() function.

        Args:
            batch_size: The batch size.
            train_images: The training images.
            train_labels: The training labels.

        Returns:
            bytes: The training secret.
        """
        self.current_iteration += 1
        train_loss, train_accuracy = -1.0, -1.0  # initialization values
        training_secret = hashlib.sha256("training_secret".encode("utf-8")).digest()
        start_idx_batch = self.current_iteration * batch_size  # branch starts here
        for i in range(batch_size):
            start_idx_sample = start_idx_batch + i  # sample starts here
            end_idx_sample = start_idx_sample + 1  # sample ends here
            train_loss, train_accuracy = self.model.train_on_batch(
                train_images[start_idx_sample:end_idx_sample],
                train_labels[start_idx_sample:end_idx_sample],
            )
            train_loss_bytes = struct.pack("!f", train_loss)
            training_secret = hashlib.sha256(
                train_loss_bytes + training_secret
            ).digest()
        logger.debug(
            f"{self.owner_name} Iteration {self.current_iteration} - Loss: "
            f"{train_loss}, Accuracy: {train_accuracy}"
        )
        return training_secret

    def get_hashed_serialization(self) -> str:
        hash_object = hashlib.sha256()
        for b in self.model.get_weights():
            hash_object.update(b.tobytes())
        model_hash = hash_object.hexdigest()
        return model_hash

    def get_id_s(self) -> str:
        """Get stage identifier."""
        return f"{self.id}:{self.current_iteration}"
