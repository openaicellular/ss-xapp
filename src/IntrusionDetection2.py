from influxdb import InfluxDBClient
import time
import signal
import os
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from datetime import datetime, timedelta

import gc
import sys

torch.set_num_threads(1)

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define parameters
seq_length = 10 
hidden_dim = 64
latent_dim = 32
batch_size = 32
num_epochs = 50
learning_rate = 0.001

counter = 1
client = None

malicious = []

trained = False
use_influx_data = True  # ✅ Default to using InfluxDB data

n_features = 3  # Adjust based on the number of features (e.g., tx_pkts, tx_error, cqi)

# RNN Autoencoder model
class RNN_Autoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dim, latent_dim):
        super(RNN_Autoencoder, self).__init__()
        self.encoder_rnn = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.hidden_to_latent = nn.Linear(hidden_dim, latent_dim)
        self.latent_to_hidden = nn.Linear(latent_dim, input_dim)
        self.decoder_rnn = nn.LSTM(hidden_dim, input_dim, batch_first=True)

    def forward(self, x):
        # Encoder
        _, (h, _) = self.encoder_rnn(x)
        latent = self.hidden_to_latent(h[-1])
        h_decoded = self.latent_to_hidden(latent).unsqueeze(0)
        c_decoded = torch.zeros_like(h_decoded)
        decoder_input = torch.zeros(x.size(0), x.size(1), hidden_dim, device=x.device)
        x_reconstructed, _ = self.decoder_rnn(decoder_input, (h_decoded, c_decoded))

        del latent, h_decoded, c_decoded, decoder_input
        gc.collect()

        return x_reconstructed

# Initialize model
model = RNN_Autoencoder(input_dim=n_features, hidden_dim=hidden_dim, latent_dim=latent_dim).to(device)

model_path = "autoencoder_random_data.pth"

if os.path.exists(model_path):
    model.load_state_dict(torch.load(model_path, map_location=device))
    print("Model loaded successfully", flush=True)
else:
    torch.save(model.state_dict(), model_path)
    print("Initialized model with random weights and saved.", flush=True)

model.eval()

def generate_random_data(seq_length, num_sequences, n_features):
    data = np.random.rand(num_sequences * seq_length, n_features).astype(np.float32)
    return data

# Data preparation (random)
def gather_random_data(seq_length, num_sequences, n_features):
    data_array = generate_random_data(seq_length, num_sequences, n_features)

    num_sequences = len(data_array) // seq_length
    data_array = data_array[:num_sequences * seq_length].reshape(num_sequences, seq_length, n_features)

    print(f"Generated data array shape: {data_array.shape}", flush=True)

    data_tensor = torch.empty(data_array.shape, dtype=torch.float32)

    for i in range(data_array.shape[0]):
        for j in range(data_array.shape[1]):
            for k in range(data_array.shape[2]):
                data_tensor[i, j, k] = float(data_array[i, j, k])

    return data_tensor

# Inference and anomaly detection
def detect_anomalies(model, data_tensor, threshold=0.01):
    model.eval()
    with torch.no_grad():
        data_tensor = data_tensor.to(device)
        reconstructed = model(data_tensor)
        mse = torch.mean((data_tensor - reconstructed) ** 2, dim=(1, 2))
        anomalies = (mse > threshold).nonzero(as_tuple=True)[0]
        if len(anomalies) > 0:
            print(f"Anomalies detected at indices: {anomalies.tolist()}", flush=True)
            return int(anomalies[0])  # Simulated RNTI
        else:
            return -1

# Main entry point
def fetchData():
    print("-- FETCHING DATA FROM INFLUXDB OR RANDOM --", flush=True)

    global client
    global counter

    try:
        if client is None:
            client = InfluxDBClient(
                host='ricplt-influxdb.ricplt.svc.cluster.local',
                port=8086
            )
            client.switch_database('Data_Collector')
    except Exception as e:
        print("IntrusionDetection: Error connecting to InfluxDB", flush=True)
        print("Error Message:", e, flush=True)

    try:
        if use_influx_data:
            # Replace this with actual InfluxDB query if available
            print("Using dummy random data for now (Influx fetch not implemented).", flush=True)
            data_tensor = gather_random_data(seq_length, 20, n_features)
        else:
            data_tensor = gather_random_data(seq_length, 20, n_features)

        result = detect_anomalies(model, data_tensor, threshold=0.01)
        return result

    except Exception as e:
        print("Intrusion Detection: Error during inference", flush=True)
        print("Error Message:", e, flush=True)

    counter += 1
    return -1
