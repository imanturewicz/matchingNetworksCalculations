import numpy as np
import matplotlib.pyplot as plt
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
    filename = f"L-Section_Solution_{solution_number}.svg"
    
    with schemdraw.Drawing(show=False) as d:
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
        
        # *** CORRECTED LINE ***
        # The proper method to save the file is .save().
        d.save(filename)
    
    print(f"  🖼️  Circuit diagram saved as: {filename}")


# --- Network Calculation Functions ---
# (calculate_l_section is slightly modified to print the save confirmation)
def calculate_l_section(frequency_hz, z_source, z_load):
    # ... (all the calculation logic at the beginning of the function is unchanged) ...
    omega = 2 * np.pi * frequency_hz
    Rs, Xs = z_source.real, z_source.imag
    Rl, Xl = z_load.real, z_load.imag

    def solve_match(r_s, x_s, r_l, x_l):
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

    print("\n-------------------------------------------")
    print(" L-Section Matching Network Solutions")
    print(f" Matching Zs = {z_source} Ω to Zl = {z_load} Ω @ {frequency_hz / 1e6} MHz")
    print("-------------------------------------------\n")

    solutions1, error1 = solve_match(Rs, Xs, Rl, Xl)
    solutions2, error2 = solve_match(Rl, Xl, Rs, Xs)
    
    found_solution = False

    if not solutions1 and not solutions2:
        print(f"❌ No L-section match possible. Reason: {error1 or error2}")
        return

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
                found_solution = True
                draw_l_section(sol_num, z_source, z_load, shunt_val, series_val, 'shunt_source')
    else:
        print(f"-> No solutions found for this topology. ({error1})")
    
    print("\n" + "="*43 + "\n")

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
                found_solution = True
                draw_l_section(sol_num, z_source, z_load, shunt_val, series_val, 'shunt_load')
    else:
        print(f"-> No solutions found for this topology. ({error2})")
    
    print("\n-------------------------------------------")

    # *** KEY CHANGE: Show all generated plots at once ***
    if found_solution:
        print("Displaying all valid circuit diagrams...")
        plt.show()


# --- Main execution ---
# (The rest of your script is unchanged)
def calculate_pi_section(frequency_hz, z_source, z_load, q_max):
    print("\n-> Pi-Section Calculator Called (Not Implemented)")
    pass

def draw_t_section(solution_number, z_source, z_load, xa_comp, xb_comp, xc_comp):
    """
    Draws the T-section circuit and saves it to a file, just like the L-section.
    Xa is series at source, Xb is series at load, Xc is shunt.
    """
    filename = f"T-Section_Solution_{solution_number}.svg"

    with schemdraw.Drawing(show=False) as d:
        d.config(unit=3)
        # We do NOT set a title, just like in the L-section code
        
        d.add(elm.SourceV().label('$Z_S$\n' + f'{z_source.real:.1f} + {z_source.imag:.1f}j Ω', loc='bottom'))
        
        # Element Xa (Series at Source)
        el_a = elm.Capacitor if 'pF' in xa_comp else elm.Inductor
        d.add(el_a().right().label(xa_comp, loc='bottom'))
        
        # Element Xc (Shunt)
        d.push()
        el_c = elm.Capacitor if 'pF' in xc_comp else elm.Inductor
        d.add(el_c().down().label(xc_comp, loc='bottom'))
        d.add(elm.Ground())
        d.pop()
        
        # Element Xb (Series at Load)
        el_b = elm.Capacitor if 'pF' in xb_comp else elm.Inductor
        d.add(el_b().right().label(xb_comp, loc='bottom'))
        
        d.add(elm.Resistor().right().label('$Z_L$\n' + f'{z_load.real:.1f} + {z_load.imag:.1f}j Ω', loc='bottom'))

        # The proper method to save the file is .save()
        d.save(filename)
    
    print(f"  🖼️  Circuit diagram saved as: {filename}")

# --- REPLACED: T-Section Calculation Function ---
def calculate_t_section(frequency_hz, z_source, z_load, q_max):
    """
    Calculates and displays the possible T-section matching networks.
    """
    omega = 2 * np.pi * frequency_hz
    Rs, Xs = z_source.real, z_source.imag
    Rl, Xl = z_load.real, z_load.imag

    def solve_t_math(r_s, x_s, r_l, x_l, q_val):
        """
        Core math solver based on the Rl < Rs formulas.
        Returns a list of solutions: [{'Xa': val, 'Xb': val, 'Xc': val}, ...]
        """
        all_solutions = []
        
        # 1. Calculate the two possible Xb values
        Xb_list = [
            (q_val * r_l - x_l),
            (-q_val * r_l - x_l)
        ]
        
        denominator_Xc = 2 * (r_l - r_s)
        if abs(denominator_Xc) < 1e-9:
            # This happens if Rs == Rl. The provided formulas are not
            # applicable. A different approach (e.g., Pi-network) is needed.
            return [], "Rs is equal to Rl. Cannot solve with these formulas."
        
        for Xb in Xb_list:
            Xb_plus_Xl = Xb + x_l
            
            # 2. Calculate Delta
            # Delta = 4*Rs*(Rs*(Xb+Xl)^2+(Rl-Rs)(Rl^2+(Xb+Xl)^2))
            term1 = r_s * (Xb_plus_Xl)**2
            term2 = (r_l - r_s) * (r_l**2 + (Xb_plus_Xl)**2)
            Delta = 4 * r_s * (term1 + term2)
            
            if Delta < 0:
                # No real solution for Xc with this Xb, so we skip
                continue
            
            # 3. Calculate Xc values
            sqrt_Delta = np.sqrt(Delta)
            numerator_base_Xc = 2 * r_s * Xb_plus_Xl
            
            Xc_list = [
                (numerator_base_Xc + sqrt_Delta) / denominator_Xc,
                (numerator_base_Xc - sqrt_Delta) / denominator_Xc
            ]
            
            for Xc in Xc_list:
                # 4. Calculate Xa for this (Xb, Xc) pair
                Xc_plus_Xb_plus_Xl = Xc + Xb + Xl
                
                numerator_Xa = Xc * (r_l**2 + Xb_plus_Xl * Xc_plus_Xb_plus_Xl)
                denominator_Xa = r_l**2 + Xc_plus_Xb_plus_Xl**2
                
                if abs(denominator_Xa) < 1e-9:
                    Xa = np.nan # Solution is invalid
                else:
                    Xa = -x_s - (numerator_Xa / denominator_Xa)
                
                if not np.isnan(Xa):
                    all_solutions.append({'Xa': Xa, 'Xb': Xb, 'Xc': Xc})
                    
        return all_solutions, None

    # --- Main Calculation and Display Logic ---
    print("\n-------------------------------------------")
    print(" T-Section Matching Network Solutions")
    print(f" Matching Zs = {z_source} Ω to Zl = {z_load} Ω @ {frequency_hz / 1e6} MHz")
    print(f" Using Q_max = {q_max:.2f}")
    print("-------------------------------------------\n")

    if abs(Rl - Rs) < 1e-9:
        print("❌ Rs is equal to Rl. The T-network formulas provided are not suitable.")
        print("   Consider using an L-section (if reactances allow) or a Pi-network.")
        return

    solutions = []
    topology = ""
    
    if Rl < Rs:
        # Standard case, formulas apply directly
        topology = "standard"
        solutions, error = solve_t_math(Rs, Xs, Rl, Xl, q_max)
    
    elif Rl > Rs:
        # Swapped case. We swap Zs and Zl for the calculation.
        topology = "swapped"
        # Note: The math function still uses (Rs, Xs, Rl, Xl) as variable names,
        # but we are passing the *values* from Zl and Zs into them.
        solutions, error = solve_t_math(Rl, Xl, Rs, Xs, q_max)
        
    if error:
        print(f"❌ Calculation error: {error}")
        return
        
    if not solutions:
        print("❌ No real solutions found for these parameters and Q_max.")
        return

    found_solution = False
    sol_num = 1
    
    for sol in solutions:
        found_solution = True
        
        if topology == "standard":
            # Labels match the formulas directly
            xa_val = sol['Xa']
            xb_val = sol['Xb']
            xc_val = sol['Xc']
            
            xa_comp = get_component_value(xa_val, omega)
            xb_comp = get_component_value(xb_val, omega)
            xc_comp = get_component_value(xc_val, omega)

            print(f"--- Solution {sol_num} (Topology Rl < Rs) ---")
            print(f"  Series (at Zs):   {xa_comp}")
            print(f"  Shunt (middle):   {xc_comp}")
            print(f"  Series (at Zl):   {xb_comp}")
            
        elif topology == "swapped":
            # Labels are swapped!
            # 'Xa' from the math is at the "new" source, (original load)
            # 'Xb' from the math is at the "new" load, (original source)
            xa_val = sol['Xb'] # This is the component at the original source
            xb_val = sol['Xa'] # This is the component at the original load
            xc_val = sol['Xc'] # Shunt is still shunt
            
            xa_comp = get_component_value(xa_val, omega)
            xb_comp = get_component_value(xb_val, omega)
            xc_comp = get_component_value(xc_val, omega)
            
            print(f"--- Solution {sol_num} (Topology Rl > Rs) ---")
            print(f"  Series (at Zs):   {xa_comp}")
            print(f"  Shunt (middle):   {xc_comp}")
            print(f"  Series (at Zl):   {xb_comp}")

        # Draw the network
        if 'N/A' not in [xa_comp, xb_comp, xc_comp]:
            draw_t_section(sol_num, z_source, z_load, xa_comp, xb_comp, xc_comp)
        
        sol_num += 1

    if found_solution:
        print("\nDisplaying all valid circuit diagrams...")
        plt.show()
    
    print("\n-------------------------------------------")

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
        return

    # --- Get common user inputs ---
    print("\nPlease provide the following parameters:")
    frequency_mhz = get_float_input("Operating Frequency (in MHz): ")
    z_source = get_complex_input("Source Impedance (Z_S):")
    z_load = get_complex_input("Load Impedance (Z_L):")

    frequency_hz = frequency_mhz * 1e6

    # --- Call the appropriate function based on user choice ---
    if choice == '1':
        calculate_l_section(frequency_hz, z_source, z_load)
        
    elif choice == '2' or choice == '3':
        # --- New Q-Factor Logic for π and T sections ---
        
        # 1. Calculate inherent nodal Qs
        q_s = abs(z_source.imag) / z_source.real if z_source.real > 1e-9 else float('inf')
        q_l = abs(z_load.imag) / z_load.real if z_load.real > 1e-9 else float('inf')
        
        min_required_q = max(q_s, q_l)
        
        print("\n--- Network Q Specification ---")
        print(f"Source Nodal Q (Qs) = {q_s:.2f}")
        print(f"Load Nodal Q (Ql)   = {q_l:.2f}")
        
        if min_required_q == float('inf'):
            print("❌ Error: Cannot match with a T or Pi network when Rs or Rl is zero.")
            return

        print(f"\nThe Maximum Nodal Q (Q_max) must be at least {min_required_q:.2f}")

        q_max = 0.0 # Initialize q_max outside the loop

        # *** START OF NEW LOOP ***
        while True: 
            print("\nHow do you want to specify the network Q?")
            print("  1. Maximum Nodal Q (Q_max)")
            print("  2. Total Network Q (Q_tot)")
            print("  3. Bandwidth (BW) in MHz")
            q_choice = input("Enter your choice (1-3): ")

            # 2. Get user input and calculate Q_max
            if q_choice == '1':
                q_max = get_float_input("Enter Maximum Nodal Quality Factor (Q_max): ")
            elif q_choice == '2':
                q_tot = get_float_input("Enter Total Quality Factor (Q_tot): ")
                q_max = q_tot * 2
                print(f"-> Calculated Q_max = {q_tot} * 2 = {q_max:.2f}")
            elif q_choice == '3':
                bw_mhz = get_float_input("Enter Desired Bandwidth (in MHz): ")
                if bw_mhz <= 0:
                    print("❌ Error: Bandwidth must be a positive number. Please try again.")
                    continue # Restart the loop
                q_tot = frequency_mhz / bw_mhz
                q_max = q_tot * 2
                print(f"-> Calculated Q_tot = {frequency_mhz} MHz / {bw_mhz} MHz = {q_tot:.2f}")
                print(f"-> Calculated Q_max = {q_tot:.2f} * 2 = {q_max:.2f}")
            else:
                print("❌ Invalid choice. Please try again.")
                continue # Restart the loop

            # 3. Validate the calculated Q_max
            if q_max < min_required_q:
                print("\n" + "!"*50)
                print(f"❌ ERROR: Specified Q_max ({q_max:.2f}) is too low.")
                print(f"         It must be >= {min_required_q:.2f} to absorb the source/load reactance.")
                print("         Please enter a valid Q specification.")
                print("!"*50)
                # Loop continues automatically
            else:
                print(f"✅ Q_max ({q_max:.2f}) is valid.")
                break # *** EXIT LOOP ***
        
        # 4. Call the correct placeholder function (now guaranteed to have valid q_max)
        if choice == '2':
            calculate_pi_section(frequency_hz, z_source, z_load, q_max)
        elif choice == '3':
            calculate_t_section(frequency_hz, z_source, z_load, q_max)
    
    print("\nProgram finished. Goodbye! 👋")

if __name__ == "__main__":
    main()