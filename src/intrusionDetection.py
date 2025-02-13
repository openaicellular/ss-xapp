import tensorflow as tf
import numpy as np
from tensorflow import keras
from influxdb import InfluxDBClient
import os

# Define parameters
seq_length = 10
hidden_dim = 64
latent_dim = 32
batch_size = 32
num_epochs = 50
learning_rate = 0.001
n_features = 3  # Number of features (e.g., tx_pkts, tx_error, cqi)

client = None
trained = False

# Define the RNN Autoencoder using TensorFlow
class RNN_Autoencoder(tf.keras.Model):
    def __init__(self, input_dim, hidden_dim, latent_dim):
        super(RNN_Autoencoder, self).__init__()
        # Encoder
        self.encoder_rnn = tf.keras.layers.LSTM(hidden_dim, return_sequences=False, return_state=True)
        self.hidden_to_latent = tf.keras.layers.Dense(latent_dim)

        # Decoder
        self.latent_to_hidden = tf.keras.layers.Dense(hidden_dim)
        self.decoder_rnn = tf.keras.layers.LSTM(hidden_dim, return_sequences=True)
        self.output_layer = tf.keras.layers.TimeDistributed(tf.keras.layers.Dense(input_dim))

    def call(self, inputs):
        # Encoder
        _, h, c = self.encoder_rnn(inputs)
        latent = self.hidden_to_latent(h)

        # Decoder
        hidden_state = self.latent_to_hidden(latent)
        repeated_hidden = tf.repeat(tf.expand_dims(hidden_state, 1), seq_length, axis=1)
        decoded = self.decoder_rnn(repeated_hidden)
        output = self.output_layer(decoded)
        return output

# Data fetching and preprocessing
def fetchData():

    # Setting up environment variables
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"

    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)

    print("-- FETCHING DATA FROM INFLUXDB --", flush=True)
    print("TensorFlow running on:", tf.config.list_physical_devices(), flush=True)

    global client, trained

    # Connect to InfluxDB
    # try:
    #     if client is None:
    #         client = InfluxDBClient(host='ricplt-influxdb.ricplt.svc.cluster.local', port=8086)
    #         client.switch_database('Data_Collector')
    # except Exception as e:
    #     print("Error connecting to InfluxDB", e, flush=True)

    # try:
    #     if not trained:
    #         run_autoencoder_influxdb(client)
    #         print("Training finished", flush=True)

    #     result = run_evaluation(client)
    #     return result
    # except Exception as e:
    #     print("Error occurred during training or evaluation", e, flush=True)

    inputs = tf.keras.Input(shape=(10,))
    dense1 = tf.keras.layers.Dense(64, activation='relu')(inputs)
    outputs = tf.keras.layers.Dense(1)(dense1)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)

    print("Minimal model created successfully!", flush=True)

    return -1

def gatherData(client):
    query = '''
        SELECT tx_pkts, tx_errors, dl_cqi
        FROM ue
        WHERE report_num >= 1 and report_num <= 10
    '''
    result = client.query(query)
    data_list = list(result.get_points())

    if not data_list:
        print("No data available for the current report.", flush=True)
        return None

    data_values = [[point.get('tx_pkts', 0), point.get('tx_errors', 0), point.get('dl_cqi', 0)] for point in data_list]
    data_array = np.array(data_values, dtype=np.float32)

    # Normalize data
    data_min = np.min(data_array, axis=0)
    data_max = np.max(data_array, axis=0)
    data_array = (data_array - data_min) / (data_max - data_min + 1e-8)

    if len(data_array) < seq_length:
        print("Not enough data for a full sequence.", flush=True)
        return None

    num_sequences = len(data_array) // seq_length
    data_array = data_array[:num_sequences * seq_length].reshape(num_sequences, seq_length, n_features)
    return data_array

def run_autoencoder_influxdb(client):
    global trained

    # Initialize model
    model = RNN_Autoencoder(input_dim=n_features, hidden_dim=hidden_dim, latent_dim=latent_dim)
    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    loss_fn = tf.keras.losses.MeanSquaredError()

    # Gather data
    data_array = gatherData(client)
    if data_array is None:
        return

    dataset = tf.data.Dataset.from_tensor_slices((data_array, data_array))
    dataset = dataset.batch(batch_size).shuffle(1000)

    # Training loop
    print("Starting training...", flush=True)
    for epoch in range(num_epochs):
        epoch_loss = 0
        for batch_data, _ in dataset:
            with tf.GradientTape() as tape:
                print("Before model", flush=True)
                reconstructed = model(batch_data)
                print("After model", flush=True)
                loss = loss_fn(batch_data, reconstructed)

            gradients = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(gradients, model.trainable_variables))
            epoch_loss += loss.numpy()

        print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {epoch_loss:.4f}")

    # Save the trained model
    model.save_weights("autoencoder_model")
    trained = True


def run_evaluation(client):
    # Load model
    model = RNN_Autoencoder(input_dim=n_features, hidden_dim=hidden_dim, latent_dim=latent_dim)
    model.load_weights("autoencoder_model")

    data_array = gatherData(client)
    if data_array is None:
        return -1

    dataset = tf.data.Dataset.from_tensor_slices((data_array, data_array))
    dataset = dataset.batch(batch_size)

    # Evaluation
    print("Starting evaluation...", flush=True)
    reconstruction_errors = []
    threshold = 0.05

    for batch_data, _ in dataset:
        reconstructed = model(batch_data)
        errors = tf.reduce_mean(tf.square(batch_data - reconstructed), axis=(1, 2)).numpy()
        reconstruction_errors.extend(errors)

    for idx, error in enumerate(reconstruction_errors):
        probability = (error / threshold) * 100
        if error > threshold:
            print(f"Sequence {idx + 1}: Anomaly detected with probability {probability:.2f}%.", flush=True)
        else:
            print(f"Sequence {idx + 1}: Normal data with probability {probability:.2f}%.", flush=True)

    return -1
