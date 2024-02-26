import numpy as np
import matplotlib.pyplot as plt

# Read the data from the iperf3 text file using NumPy
data1 = np.genfromtxt('ue1-iperf3-file', skip_header=4, usecols=(4, 5, 6,))
data2 = np.genfromtxt('ue2-iperf3-file', skip_header=4, usecols=(4, 5, 6,))

# Extract the columns into separate variables
transfer1 = data1[:, 0]
bandwidth1 = data1[:, 2]

transfer2 = data2[:, 0]
bandwidth2 = data2[:, 2]

for i in range(len(transfer1)):
    if transfer1[i] > 10:
        transfer1[i] /= 1024

    if bandwidth1[i] > 90:
        bandwidth1[i] /= 1024

for i in range(len(transfer2)):
    if transfer2[i] > 10:
        transfer2[i] /= 1024

    if bandwidth2[i] > 90:
        bandwidth2[i] /= 1024

#print(bandwidth)
#print(transfer)

# Plot the data
plt.plot( bandwidth1, label='Bandwidth1', linewidth=1)
#plt.plot( transfer1, label='Transfer1', linewidth=1)

plt.plot( bandwidth2, label = 'Bandwidth2', linewidth=1)
#plt.plot( transfer2, label = 'Transfer2', linewidth=1)

plt.xlabel('Time (sec)')
plt.ylabel('Throughput')
plt.legend(['Bandwidth1 - Mbits/sec', 'Bandwidth2 - Mbits/sec'])

#plt.savefig('Rate_Leg_Mali_SharesController.png')
#plt.savefig('Rate_Leg_Mali_SharesController.eps')
#plt.savefig('Rate_Leg_Mali_SharesController.pdf')

plt.show()
