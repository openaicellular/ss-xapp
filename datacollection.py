import pandas as pd
import re

# Read the log file and extract relevant fields
file_path = "file_name"
output_file = "file_name.csv"
columns = {
    "available_dl_prbs": [],
    "available_ul_prbs": [],
    "dl_bytes": [],
    "ul_bytes": [],
    "dl_prbs": [],
    "ul_prbs": [],
    "tx_pkts": [],
    "tx_errors": [],
    "rx_pkts": [],
    "rx_errors": [],
    "rx_brate": [],
    "dl_cqi": [],
    "dl_ri": [],
    "dl_pmi": [],
    "ul_phr": [],
    "ul_sinr": [],
    "ul_mcs": [],
    "ul_samples": [],
    "dl_mcs": [],
    "dl_samples": []
    # Add more fields as needed
}

pattern = r"available_dl_prbs=(\d+)\s+available_ul_prbs=(\d+)\s+ue\[\d+\]={dl_bytes=(\d+),ul_bytes=(\d+),dl_prbs=(\d+),ul_prbs=(\d+),tx_pkts=(\d+),tx_errors=(\d+),tx_brate=(\d+),rx_pkts=(\d+),rx_errors=(\d+),rx_brate=(\d+),dl_cqi=(\d+),dl_ri=(\d+),dl_pmi=(\d+),ul_phr=(\d+),ul_sinr=([\d.]+),ul_mcs=([\d.]+),ul_samples=(\d+),dl_mcs=([\d.]+),dl_samples=(\d+)"
with open(file_path, "r") as file:
    for line in file:
        match = re.search(pattern, line)
        if match:
            available_dl_prbs = match.group(1)
            available_ul_prbs = match.group(2)
            dl_bytes = match.group(3)
            ul_bytes = match.group(4)
            dl_prbs = match.group(5)
            ul_prbs = match.group(6)
            tx_pkts = match.group(7)
            tx_errors = match.group(8)
            tx_brate = match.group(9)
            rx_pkts = match.group(10)
            rx_errors = match.group(11)
            rx_brate = match.group(12)
            dl_cqi = match.group(13)
            dl_ri = match.group(14)
            dl_pmi = match.group(15)
            ul_phr = match.group(16)
            ul_sinr = match.group(17)
            ul_mcs = match.group(18)
            ul_samples = match.group(19)
            dl_mcs = match.group(20)
            dl_samples = match.group(21)
            columns["available_dl_prbs"].append(available_dl_prbs)
            columns["available_ul_prbs"].append(available_ul_prbs)
            columns["dl_bytes"].append(dl_bytes)
            columns["ul_bytes"].append(ul_bytes)
            columns["dl_prbs"].append(dl_prbs)
            columns["ul_prbs"].append(ul_prbs)
            columns["tx_pkts"].append(tx_pkts)
            columns["tx_errors"].append(tx_errors)
            columns["rx_pkts"].append(rx_pkts)
            columns["rx_errors"].append(rx_errors)
            columns["rx_brate"].append(rx_brate)
            columns["dl_cqi"].append(dl_cqi)
            columns["dl_ri"].append(dl_ri)
            columns["dl_pmi"].append(dl_pmi)
            columns["ul_phr"].append(ul_phr)
            columns["ul_sinr"].append(ul_sinr)
            columns["ul_mcs"].append(ul_mcs)
            columns["ul_samples"].append(ul_samples)
            columns["dl_mcs"].append(dl_mcs)
            columns["dl_samples"].append(dl_samples)

# Create a DataFrame from the extracted fields
df = pd.DataFrame(columns)
df.to_csv(output_file, index=False)

# Print the DataFrame
print(df)

