import numpy as np

# --- Global Helper Functions --- 

def get_float_input(prompt):
    """A helper function to safely get a floating-point number from the user."""
    # ... (code is unchanged)
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def get_complex_input(prompt):
    """A helper function to safely get a complex impedance (R + jX) from the user."""
    # ... (code is unchanged)
    print(prompt)
    while True:
        try:
            real_part = float(input("  Enter the Real part (R): "))
            imag_part = float(input("  Enter the Imaginary part (X): "))
            return complex(real_part, imag_part)
        except ValueError:
            print("Invalid input. Please enter valid numbers for the real and imaginary parts.")

def get_component_value(reactance, omega):
    """
    (REUSABLE) Converts a reactance value into a practical component value (L or C).
    """
    if np.isnan(reactance) or abs(omega) < 1e-12:
        return "N/A"
    
    if reactance > 0:
        # Positive reactance is an inductor: X = ωL -> L = X/ω
        inductance_nH = (reactance / omega) * 1e9 # Convert H to nH
        return f"{inductance_nH:.3f} nH (Inductor)"
    elif reactance < 0:
        # Negative reactance is a capacitor: X = -1/(ωC) -> C = -1/(ωX)
        capacitance_pF = (-1 / (omega * reactance)) * 1e12 # Convert F to pF
        return f"{capacitance_pF:.3f} pF (Capacitor)"
    else:
        return "0 Ω (short/wire)"

# --- Network Calculation Functions ---

def calculate_l_section(frequency_hz, z_source, z_load):
    """
    Calculates and displays the four possible L-section matching networks.
    """
    omega = 2 * np.pi * frequency_hz
    Rs, Xs = z_source.real, z_source.imag
    Rl, Xl = z_load.real, z_load.imag

    def solve_match(r_s, x_s, r_l, x_l):
        """
        (L-SECTION SPECIFIC) Core calculation to find the two reactance solutions.
        This logic is unique to the L-section and is kept encapsulated here.
        """
        # ... (code for this inner function is unchanged)
        solutions = []
        D = (4 * (r_s**2) * (x_l**2)) - \
            (4 * (r_s**2) * (r_l**2 + x_l**2)) + \
            (4 * r_s * r_l * (r_s**2 + x_s**2))

        if D < 0:
            return solutions, "No real solution exists (Discriminant is negative)."

        sqrt_D = np.sqrt(D)
        denominator = 2 * r_s

        if abs(denominator) < 1e-12:
            return solutions, "Source resistance cannot be zero."

        X_b1 = (-2 * r_s * x_l + sqrt_D) / denominator
        X_b2 = (-2 * r_s * x_l - sqrt_D) / denominator

        def calc_Xa(Xb):
            Rs2_Xs2 = r_s**2 + x_s**2
            Xb_Xl = Xb + x_l
            Rl2_XbXl2 = r_l**2 + Xb_Xl**2
            numerator = -(Rs2_Xs2 * Rl2_XbXl2)
            denominator = (x_s * Rl2_XbXl2) + (Xb_Xl * Rs2_Xs2)
            return numerator / denominator if abs(denominator) > 1e-12 else np.nan

        solutions.append({'X_b': X_b1, 'X_a': calc_Xa(X_b1)})
        solutions.append({'X_b': X_b2, 'X_a': calc_Xa(X_b2)})
        
        return solutions, None

    # --- Main Calculation & Display Logic ---
    # ... (This part is unchanged, it now calls the global get_component_value)
    
    print("\n-------------------------------------------")
    print(" L-Section Matching Network Solutions")
    print(f" Matching Zs = {z_source} Ω to Zl = {z_load} Ω @ {frequency_hz / 1e6} MHz")
    print("-------------------------------------------\n")

    solutions1, error1 = solve_match(Rs, Xs, Rl, Xl)
    solutions2, error2 = solve_match(Rl, Xl, Rs, Xs)

    if not solutions1 and not solutions2:
        print(f"❌ No L-section match possible. Reason: {error1 or error2}")
        return

    print("## Topology 1: Shunt Component at SOURCE, Series at LOAD")
    if solutions1:
        for i, sol in enumerate(solutions1):
            print(f"--- Solution {i+1} ---")
            print(f"  Shunt Reactance (at Zs): {sol['X_a']:.3f} Ω")
            print(f"  -> Shunt Component: {get_component_value(sol['X_a'], omega)}")
            print(f"  Series Reactance (at Zl): {sol['X_b']:.3f} Ω")
            print(f"  -> Series Component: {get_component_value(sol['X_b'], omega)}")
    else:
        print(f"-> No solutions found for this topology. ({error1})")
    
    print("\n" + "="*43 + "\n")

    print("## Topology 2: Shunt Component at LOAD, Series at SOURCE")
    if solutions2:
        for i, sol in enumerate(solutions2):
            print(f"--- Solution {i+3} ---")
            print(f"  Series Reactance (at Zs): {sol['X_b']:.3f} Ω")
            print(f"  -> Series Component: {get_component_value(sol['X_b'], omega)}")
            print(f"  Shunt Reactance (at Zl): {sol['X_a']:.3f} Ω")
            print(f"  -> Shunt Component: {get_component_value(sol['X_a'], omega)}")
    else:
        print(f"-> No solutions found for this topology. ({error2})")
    
    print("\n-------------------------------------------")

def calculate_pi_section(frequency_hz, z_source, z_load, q_max):
    """
    Calculates the component values for a π-section network.
    """
    print("\n-------------------------------------------")
    print("-> Pi-Section Calculator Called")
    print(f"-> Freq: {frequency_hz / 1e6} MHz, Z_source: {z_source} Ω, Z_load: {z_load} Ω, Q_max: {q_max}")
    omega = 2 * np.pi * frequency_hz
    print(f"   Angular Frequency (ω): {omega:.2f} rad/s")
    print("   (Calculation logic not yet implemented.)")
    print("-------------------------------------------\n")
    pass

def calculate_t_section(frequency_hz, z_source, z_load, q_max):
    """
    Calculates the component values for a T-section network.
    """
    print("\n-------------------------------------------")
    print("-> T-Section Calculator Called")
    print(f"-> Freq: {frequency_hz / 1e6} MHz, Z_source: {z_source} Ω, Z_load: {z_load} Ω, Q_max: {q_max}")
    omega = 2 * np.pi * frequency_hz
    print(f"   Angular Frequency (ω): {omega:.2f} rad/s")
    print("   (Calculation logic not yet implemented.)")
    print("-------------------------------------------\n")
    pass

# --- Main Program Logic ---

def main():
    """Main function to run the matching network tool."""
    print("=============================================")
    print(" Passive Matching Network Design Tool 📡")
    print("=============================================")

    print("\nSelect the matching network topology:")
    print("  1. L-Section")
    print("  2. π-Section (Pi-Section)")
    print("  3. T-Section")

    choice = input("Enter your choice (1-3): ")

    if choice not in ['1', '2', '3']:
        print("Invalid choice. Please run the program again.")
        return # Exit the program if choice is invalid

    # --- Get common user inputs ---
    print("\nPlease provide the following parameters:")
    frequency_mhz = get_float_input("Operating Frequency (in MHz): ")
    z_source = get_complex_input("Source Impedance (Z_S):")
    z_load = get_complex_input("Load Impedance (Z_L):")

    # Convert MHz to Hz for calculations
    frequency_hz = frequency_mhz * 1e6

    # --- Call the appropriate function based on user choice ---
    if choice == '1':
        calculate_l_section(frequency_hz, z_source, z_load)
    elif choice == '2':
        q_max = get_float_input("Maximum Nodal Quality Factor (Q_max): ")
        calculate_pi_section(frequency_hz, z_source, z_load, q_max)
    elif choice == '3':
        q_max = get_float_input("Maximum Nodal Quality Factor (Q_max): ")
        calculate_t_section(frequency_hz, z_source, z_load, q_max)
    
    print("Program finished. Goodbye! 👋")

if __name__ == "__main__":
    main()