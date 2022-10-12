import warnings
import flwr as fl
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Dense, Dropout
from tensorflow.python.keras import optimizers

from sklearn.neural_network import MLPClassifier

import utils

client_num = 1
sv = "127.0.0.1:8080"

if __name__ == "__main__":
    # Load MNIST dataset from https://www.openml.org/d/554
    (X_train, y_train), (X_test, y_test) = utils.load_data(client_num)
    #(X_train, y_train), (X_test, y_test) = utils.load_mnist()

    # Split train set into 10 partitions and randomly use one for training. 
    #partition_id = np.random.choice(10)
    #(X_t1, y_t1) = utils.partition(X_train, y_train, 10)[partition_id]

    # Create LogisticRegression Model
    #model = LogisticRegression(
    #    penalty="l2",
    #    max_iter=20,  # local epoch
    #    warm_start=True,  # prevent refreshing weights when fitting
    #)
    model = utils.create_model()

    # Setting initial parameters, akin to model.compile for keras models
    utils.set_initial_params(model)

    # Define Flower client
    class ClassClient(fl.client.NumPyClient):        
        def get_parameters(self, config):  # type: ignore
            return utils.get_model_parameters(model)

        def fit(self, parameters, config):  # type: ignore
            utils.set_model_params(model, parameters)
            # Ignore convergence failure due to low local epochs
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(X_train, y_train)
            print(f"Training finished for round {config['server_round']}")
            return utils.get_model_parameters(model), len(X_train), {}

        def evaluate(self, parameters, config):  # type: ignore
            utils.set_model_params(model, parameters)
            loss = log_loss(y_test, model.predict_proba(X_test))
            accuracy = model.score(X_test, y_test)
            return loss, len(X_test), {"accuracy": accuracy}

    # Start Flower client
    fl.client.start_numpy_client(server_address=sv, client=ClassClient())