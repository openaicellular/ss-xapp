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

def fetchData():
    print("-- FETCHING DATA FROM INFLUXDB --", flush=True)

    global client
    global counter
    global trained

    # Connecting to database
    try:
        if client == None:
            client = InfluxDBClient(
                host='ricplt-influxdb.ricplt.svc.cluster.local',
                port=8086
            )
            client.switch_database('Data_Collector')
    except Exception as e:
        print("IntrusionDetection: Error connecting to InfluxDB", flush=True)
        print("Error Message:", e, flush=True)

    try:
        if not trained:
            run_autoencoder_influxdb(client, counter)
            print("Training finished", flush=True)
        return -1
    
    except Exception as e:
        print("Intrusion Detection: Error occured when trying to train model", flush=True)
        print("Error Message:", e, flush=True)

    counter += 1
    return -1

def generate_random_data(seq_length, num_sequences, n_features):
    data = np.random.rand(num_sequences * seq_length, n_features).astype(np.float32)
    return data

# Data preparation
def gather_random_data(seq_length, num_sequences, n_features):
    data_array = generate_random_data(seq_length, num_sequences, n_features)

    # Reshape into sequences for RNN
    num_sequences = len(data_array) // seq_length
    data_array = data_array[:num_sequences * seq_length].reshape(num_sequences, seq_length, n_features)

    print(f"Generated data array shape: {data_array.shape}", flush=True)

    data_tensor = torch.empty(data_array.shape, dtype=torch.float32)

    # Convert the numpy array manually to a Tensor due to hanging issues.
    for i in range(data_array.shape[0]):
        for j in range(data_array.shape[1]):
            for k in range(data_array.shape[2]):
                data_tensor[i, j, k] = float(data_array[i, j, k])

    return data_tensor

def run_autoencoder_influxdb(client, reportCounter): # Training

    global batch_size
    global num_epochs
    global device

    # Initialize model, loss, and optimizer
    model = RNN_Autoencoder(input_dim=n_features, hidden_dim=64, latent_dim=32).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    num_sequences = 1000  # Number of sequences for training
    data_tensor = gather_random_data(seq_length, num_sequences, n_features)

    # DataLoader preparation
    labels = torch.zeros(data_tensor.size(0))
    dataset = TensorDataset(data_tensor, labels)
    train_loader = DataLoader(dataset, batch_size, shuffle=True, num_workers=0)

    # Train the model
    model.train()

    print("Training the model", flush=True)

    for epoch in range(num_epochs):
        print(f"Epoch {epoch + 1}/{num_epochs} started", flush=True)
        print(f"  Model parameters before epoch: {list(model.parameters())[0][:5]}", flush=True)  # Example: print first few weights
        print(f"Epoch {epoch + 1}/{num_epochs} started. Total batches: {len(train_loader)}", flush=True)
        epoch_loss = 0.0
        for batch_idx, (batch_data, _) in enumerate(train_loader):
            print(f"Batch {batch_idx + 1}/{len(train_loader)} started", flush=True)  # Tracking batch start
            print(f"  Processing batch {batch_idx + 1}/{len(train_loader)}. Batch data shape: {batch_data.shape}", flush=True)
            batch_data = batch_data.to(device)
            print(f"  Transferred batch to device: {batch_data.device}", flush=True)  # Verify data on device
            batch_data = batch_data.to(device)

            print(f"    Running optimizer.zero_grad()", flush=True)
            optimizer.zero_grad()
            print(f"    Passing batch through the model", flush=True)
            reconstructed = model(batch_data)
            print(f"  Output from model: {reconstructed[0][:5]} (first sequence, first few values)", flush=True)  # Check example output
            print(f"    Model output shape: {reconstructed.shape}", flush=True)
            print(f"    Calculating loss", flush=True)
            loss = criterion(reconstructed, batch_data)
            print(f"    Loss: {loss.item()}", flush=True)
            print(f"    Backpropagating loss", flush=True)
            loss.backward()
            print(f"  Gradients computed for backpropagation", flush=True)  # Confirm gradients computed
            print(f"    Updating model parameters", flush=True)
            optimizer.step()
            print(f"  Optimizer updated model parameters", flush=True)  # Confirm optimizer step completed
            epoch_loss += loss.item()
            print(f"    Cumulative epoch loss: {epoch_loss}", flush=True)

            del reconstructed
            del loss

            gc.collect()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {epoch_loss:.4f}", flush=True)

    print("Training completed.", flush=True)

    print("Saving model as 'autoencoder_random_data.pth'.", flush=True)

    # Save the trained model
    torch.save(model.state_dict(), "autoencoder_random_data.pth")

    if os.path.exists("autoencoder_random_data.pth"): 
        print("Model file saved successfully.", flush=True) 
    else: 
        print("Model file not found.", flush=True)

    del model
    del optimizer
    del criterion
    del train_loader
    del data_tensor

    gc.collect()

    return -1
