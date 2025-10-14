import numpy as np
import schemdraw
import schemdraw.elements as elm

# --- Global Helper Functions ---
# (These are unchanged)
def get_float_input(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def get_complex_input(prompt):
    print(prompt)
    while True:
        try:
            real_part = float(input("  Enter the Real part (R): "))
            imag_part = float(input("  Enter the Imaginary part (X): "))
            return complex(real_part, imag_part)
        except ValueError:
            print("Invalid input. Please enter valid numbers for the real and imaginary parts.")

def get_component_value(reactance, omega):
    if np.isnan(reactance) or abs(omega) < 1e-12:
        return "N/A"
    if reactance > 0:
        inductance_nH = (reactance / omega) * 1e9
        return f"{inductance_nH:.3f} nH (L)"
    elif reactance < 0:
        capacitance_pF = (-1 / (omega * reactance)) * 1e12
        return f"{capacitance_pF:.3f} pF (C)"
    else:
        return "0 Ω"

# --- Drawing Function (MODIFIED) ---

def draw_l_section(solution_number, z_source, z_load, shunt_comp, series_comp, topology):
    """
    Draws the L-section circuit and saves it to a file.
    """
    # Define a unique filename for each solution's diagram
    filename = f"L-Section_Solution_{solution_number}.svg"
    
    with schemdraw.Drawing() as d:
        d.config(unit=3)
        d.add(elm.SourceV().label('$Z_S$\n' + f'{z_source.real:.1f} + {z_source.imag:.1f}j Ω', loc='bottom'))
        
        if topology == 'shunt_source':
            shunt_element = elm.Capacitor if 'pF' in shunt_comp else elm.Inductor
            series_element = elm.Capacitor if 'pF' in series_comp else elm.Inductor
            d.add(elm.Line().right())
            d.push()
            d.add(shunt_element().down().label(shunt_comp, loc='bottom'))
            d.add(elm.Ground())
            d.pop()
            d.add(series_element().right().label(series_comp, loc='bottom'))
        
        elif topology == 'shunt_load':
            series_element = elm.Capacitor if 'pF' in series_comp else elm.Inductor
            shunt_element = elm.Capacitor if 'pF' in shunt_comp else elm.Inductor
            d.add(series_element().right().label(series_comp, loc='bottom'))
            d.push()
            d.add(shunt_element().down().label(shunt_comp, loc='bottom'))
            d.add(elm.Ground())
            d.pop()

        d.add(elm.Resistor().right().label('$Z_L$\n' + f'{z_load.real:.1f} + {z_load.imag:.1f}j Ω', loc='bottom'))
        
        # *** KEY CHANGE: Save to file instead of showing ***
        d.save(filename)
    
    # Inform the user that the file has been saved
    print(f"  🖼️  Circuit diagram saved as: {filename}")


# --- Network Calculation Functions ---
# (calculate_l_section is slightly modified to print the save confirmation)
def calculate_l_section(frequency_hz, z_source, z_load):
    omega = 2 * np.pi * frequency_hz
    Rs, Xs = z_source.real, z_source.imag
    Rl, Xl = z_load.real, z_load.imag

    def solve_match(r_s, x_s, r_l, x_l):
        # ... (This inner function is unchanged)
        solutions = []
        D = (4 * (r_s**2) * (x_l**2)) - \
            (4 * (r_s**2) * (r_l**2 + x_l**2)) + \
            (4 * r_s * r_l * (r_s**2 + x_s**2))
        if D < 0: return solutions, "No real solution (Discriminant < 0)."
        sqrt_D = np.sqrt(D)
        denominator = 2 * r_s
        if abs(denominator) < 1e-9: return solutions, "Source resistance is zero."
        X_b1 = (-2 * r_s * x_l + sqrt_D) / denominator
        X_b2 = (-2 * r_s * x_l - sqrt_D) / denominator
        def calc_Xa(Xb):
            Rs2_Xs2 = r_s**2 + x_s**2; Xb_Xl = Xb + x_l
            Rl2_XbXl2 = r_l**2 + Xb_Xl**2
            num = -(Rs2_Xs2 * Rl2_XbXl2)
            den = (x_s * Rl2_XbXl2) + (Xb_Xl * Rs2_Xs2)
            return num / den if abs(den) > 1e-9 else np.nan
        solutions.append({'X_b': X_b1, 'X_a': calc_Xa(X_b1)})
        solutions.append({'X_b': X_b2, 'X_a': calc_Xa(X_b2)})
        return solutions, None

    # --- Main Calculation & Display Logic ---
    print("\n-------------------------------------------")
    print(" L-Section Matching Network Solutions")
    print(f" Matching Zs = {z_source} Ω to Zl = {z_load} Ω @ {frequency_hz / 1e6} MHz")
    print("-------------------------------------------\n")

    solutions1, error1 = solve_match(Rs, Xs, Rl, Xl)
    solutions2, error2 = solve_match(Rl, Xl, Rs, Xs)

    if not solutions1 and not solutions2:
        print(f"❌ No L-section match possible. Reason: {error1 or error2}")
        return

    # Display Solutions 1 & 2 (Shunt at Source)
    print("## Topology 1: Shunt Component at SOURCE, Series at LOAD")
    if solutions1:
        for i, sol in enumerate(solutions1):
            sol_num = i + 1
            shunt_val = get_component_value(sol['X_a'], omega)
            series_val = get_component_value(sol['X_b'], omega)
            print(f"--- Solution {sol_num} ---")
            print(f"  Shunt Component (at Zs): {shunt_val}")
            print(f"  Series Component (at Zl): {series_val}")
            if 'N/A' not in shunt_val and 'N/A' not in series_val:
                draw_l_section(sol_num, z_source, z_load, shunt_val, series_val, 'shunt_source')
    else:
        print(f"-> No solutions found for this topology. ({error1})")
    
    print("\n" + "="*43 + "\n")

    # Display Solutions 3 & 4 (Shunt at Load)
    print("## Topology 2: Shunt Component at LOAD, Series at SOURCE")
    if solutions2:
        for i, sol in enumerate(solutions2):
            sol_num = i + 3
            series_val = get_component_value(sol['X_b'], omega)
            shunt_val = get_component_value(sol['X_a'], omega)
            print(f"--- Solution {sol_num} ---")
            print(f"  Series Component (at Zs): {series_val}")
            print(f"  Shunt Component (at Zl): {shunt_val}")
            if 'N/A' not in shunt_val and 'N/A' not in series_val:
                draw_l_section(sol_num, z_source, z_load, shunt_val, series_val, 'shunt_load')
    else:
        print(f"-> No solutions found for this topology. ({error2})")
    
    print("\n-------------------------------------------")


# --- Main execution ---
# (The rest of your script is unchanged)
def calculate_pi_section(frequency_hz, z_source, z_load, q_max):
    print("\n-> Pi-Section Calculator Called (Not Implemented)")
    pass

def calculate_t_section(frequency_hz, z_source, z_load, q_max):
    print("\n-> T-Section Calculator Called (Not Implemented)")
    pass

def main():
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
        return
    print("\nPlease provide the following parameters:")
    frequency_mhz = get_float_input("Operating Frequency (in MHz): ")
    z_source = get_complex_input("Source Impedance (Z_S):")
    z_load = get_complex_input("Load Impedance (Z_L):")
    frequency_hz = frequency_mhz * 1e6
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