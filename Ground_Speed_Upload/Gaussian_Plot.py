import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import math
import pandas as pd

df = pd.read_csv('ASDE-X_Speed.csv')

fig, ax = plt.subplots()
ax.set_xlabel('Speed (m/s) on Whole Airport ')
mu = df['Average_Speed']
variance = df['Standard_Deviation_of_Speed']
sigma = math.sqrt(variance)
x = np.linspace(mu - 3*sigma, mu + 3*sigma, 100)
plt.plot(x, stats.norm.pdf(x, mu, sigma),color='black')
ax.annotate('Average Speed', xy=(mu, 0.175),color='black'
            )


mu = df['Arrival_Average_Speed']
variance = df['Standard_Deviation_of_Arrival_Speed']
sigma = math.sqrt(variance)
x = np.linspace(mu - 3*sigma, mu + 3*sigma, 100)
plt.plot(x, stats.norm.pdf(x, mu, sigma),color='blue')
ax.annotate('Arrival Speed', xy=(20, 0.15),color='blue'
            )




mu = df['Departure_Average_Speed']
variance = df['Standard_Deviation_of_Departure_Speed']
sigma = math.sqrt(variance)
x = np.linspace(mu - 3*sigma, mu + 3*sigma, 100)
plt.plot(x, stats.norm.pdf(x, mu, sigma),color='green')
ax.annotate('Departure Speed', xy=(8.5, 0.15),color='green'
            )


plt.savefig('Average Speed')
plt.show()