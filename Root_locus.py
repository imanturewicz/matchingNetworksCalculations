import numpy as np
import matplotlib.pyplot as plt
from control import tf, root_locus

# Define the transfer function G(s)H(s) = (s+2) / (s^2 + 2s + 2)
numerator = [1, 2]  # (s + 2)
denominator = [1, 2, 2]  # (s^2 + 2s + 2)
system = tf(numerator, denominator)

# Generate the root locus plot
plt.figure(figsize=(8, 6))
root_locus(system, grid=True)
plt.title("Root Locus of G(s)H(s) = (s+2) / (s^2 + 2s + 2)")
plt.xlabel("Real Axis")
plt.ylabel("Imaginary Axis")
plt.axhline(0, color='k', linewidth=0.8, linestyle='--')  # Imaginary axis
plt.axvline(0, color='k', linewidth=0.8, linestyle='--')  # Real axis
plt.show()