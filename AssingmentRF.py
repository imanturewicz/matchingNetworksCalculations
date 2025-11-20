import numpy as np
import matplotlib
# We DO NOT use matplotlib.use('Agg') because we want plt.show()
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm

# --- Global Helper Functions: User Input ---
def get_float_input(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("  Invalid input. Please enter a valid number.")

def get_complex_input(prompt):
    print(prompt)
    while True:
        try:
            real_part = float(input("  Enter the Real part (R): "))
            imag_part = float(input("  Enter the Imaginary part (X): "))
            return complex(real_part, imag_part)
        except ValueError:
            print("  Invalid input. Please enter valid numbers.")

# --- Global Helper Functions: Component Calculation ---

def get_component_string(reactance, omega):
    """Converts reactance to a string label (e.g., '12 nH')."""
    if np.isnan(reactance) or abs(omega) < 1e-12:
        return "N/A"
    if reactance > 0:
        inductance_nH = (reactance / omega) * 1e9
        return f"{inductance_nH:.3f} nH (L)"
    elif reactance < 0:
        capacitance_pF = (-1 / (omega * reactance)) * 1e12
        return f"{capacitance_pF:.3f} pF (C)"
    else:
        return "0 Ω (short)"

def get_numeric_component_value(reactance, omega):
    """
    Returns a tuple: (Component Type 'L'/'C', Value in Henry/Farad).
    Used for the frequency sweep simulation.
    """
    if np.isnan(reactance) or abs(omega) < 1e-12:
        return None, 0.0
    if reactance > 0:
        val = reactance / omega
        return 'L', val
    elif reactance < 0:
        val = -1 / (omega * reactance)
        return 'C', val
    else:
        return 'Short', 0.0

# --- ABCD Matrix Helper Functions ---

def get_abcd_series(z_ohms):
    return np.array([[1, z_ohms], [0, 1]], dtype=complex)

def get_abcd_shunt(z_ohms):
    if abs(z_ohms) < 1e-12: y = 1e12 
    else: y = 1 / z_ohms
    return np.array([[1, 0], [y, 1]], dtype=complex)

def get_z_component(ctype, value, omega):
    if ctype == 'L': return 1j * omega * value
    elif ctype == 'C':
        if omega == 0: return -1j * 1e12
        return 1 / (1j * omega * value)
    elif ctype == 'Short': return 0.0
    return 0.0

def calculate_insertion_loss_db(abcd_matrix, Zs, Zl):
    A, B, C, D = abcd_matrix[0, 0], abcd_matrix[0, 1], abcd_matrix[1, 0], abcd_matrix[1, 1]
    numerator = A * Zl + B + C * Zs * Zl + D * Zs
    denominator = 2 * np.sqrt(Zs.real * Zl.real)
    if denominator == 0: denominator = 1e-12
    ratio = abs(numerator) / denominator
    if ratio == 0: return 0
    return 20 * np.log10(ratio)

# --- Core Math ---
def _solve_t_pi_math(r_s, x_s, r_l, x_l, q_val):
    all_solutions = []
    Xb_list = [(q_val * r_l - x_l), (-q_val * r_l - x_l)]
    denominator_Xc = 2 * (r_l - r_s)
    if abs(denominator_Xc) < 1e-9:
        return [], "Rs/Gs is equal to Rl/Gl. Cannot solve."
    for Xb in Xb_list:
        Xb_plus_Xl = Xb + x_l
        term1 = r_s * (Xb_plus_Xl)**2
        term2 = (r_l - r_s) * (r_l**2 + (Xb_plus_Xl)**2)
        Delta = 4 * r_s * (term1 + term2)
        if Delta < 0: continue
        sqrt_Delta = np.sqrt(Delta)
        numerator_base_Xc = 2 * r_s * Xb_plus_Xl
        Xc_list = [(numerator_base_Xc + sqrt_Delta) / denominator_Xc, (numerator_base_Xc - sqrt_Delta) / denominator_Xc]
        for Xc in Xc_list:
            Xc_plus_Xb_plus_Xl = Xc + Xb + x_l
            numerator_Xa = Xc * (r_l**2 + Xb_plus_Xl * Xc_plus_Xb_plus_Xl)
            denominator_Xa = r_l**2 + Xc_plus_Xb_plus_Xl**2
            if abs(denominator_Xa) < 1e-9: Xa = np.nan
            else: Xa = -x_s - (numerator_Xa / denominator_Xa)
            if not np.isnan(Xa): all_solutions.append({'Xa': Xa, 'Xb': Xb, 'Xc': Xc})
    return all_solutions, None

# --- Drawing Functions ---

def draw_l_section(solution_number, z_source, z_load, shunt_comp, series_comp, topology):
    filename = f"L-Section_Solution_{solution_number}.svg"
    with schemdraw.Drawing(show=False) as d:
        d.config(unit=3)
        d.add(elm.SourceV().label('$Z_S$\n' + f'{z_source.real:.1f} + {z_source.imag:.1f}j Ω', loc='bottom'))
        
        if topology == 'shunt_source':
            shunt_element = elm.Capacitor if 'pF' in shunt_comp else elm.Inductor
            series_element = elm.Capacitor if 'pF' in series_comp else elm.Inductor
            d.add(elm.Line().right(d.unit * 2)) 
            d.push()
            d.add(shunt_element().down().label(shunt_comp, loc='bottom'))
            d.add(elm.Ground())
            d.pop()
            d.add(series_element().right().label(series_comp, loc='top'))
            d.add(elm.Line().right(d.unit / 2))
        elif topology == 'shunt_load':
            series_element = elm.Capacitor if 'pF' in series_comp else elm.Inductor
            shunt_element = elm.Capacitor if 'pF' in shunt_comp else elm.Inductor
            d.add(series_element().right(d.unit * 2).label(series_comp, loc='top'))
            d.push()
            d.add(shunt_element().down().label(shunt_comp, loc='bottom'))
            d.add(elm.Ground())
            d.pop()
            d.add(elm.Line().right(d.unit / 2))

        d.add(elm.Resistor().right().label('$Z_L$\n' + f'{z_load.real:.1f} + {z_load.imag:.1f}j Ω', loc='bottom'))
    print(f"  Circuit diagram generated: {filename}")

def draw_t_section(solution_number, z_source, z_load, xa_comp, xb_comp, xc_comp):
    filename = f"T-Section_Solution_{solution_number}.svg"
    with schemdraw.Drawing(show=False) as d:
        d.config(unit=3)
        d.add(elm.SourceV().label('$Z_S$\n' + f'{z_source.real:.1f} + {z_source.imag:.1f}j Ω', loc='bottom'))
        el_a = elm.Capacitor if 'pF' in xa_comp else elm.Inductor
        d.add(el_a().right(d.unit * 2).label(xa_comp, loc='top'))
        d.push()
        el_c = elm.Capacitor if 'pF' in xc_comp else elm.Inductor
        d.add(el_c().down().label(xc_comp, loc='bottom'))
        d.add(elm.Ground())
        d.pop()
        el_b = elm.Capacitor if 'pF' in xb_comp else elm.Inductor
        d.add(el_b().right().label(xb_comp, loc='top'))
        d.add(elm.Line().right(d.unit / 2))
        d.add(elm.Resistor().right().label('$Z_L$\n' + f'{z_load.real:.1f} + {z_load.imag:.1f}j Ω', loc='bottom'))
    print(f"  Circuit diagram generated: {filename}")

def draw_pi_section(solution_number, z_source, z_load, ba_comp, bb_comp, bc_comp):
    filename = f"Pi-Section_Solution_{solution_number}.svg"
    with schemdraw.Drawing(show=False) as d:
        d.config(unit=3)
        d.add(elm.SourceV().label('$Z_S$\n' + f'{z_source.real:.1f} + {z_source.imag:.1f}j Ω', loc='bottom'))
        d.add(elm.Line().right(d.unit * 2)) 
        d.push()
        el_a = elm.Capacitor if 'pF' in ba_comp else elm.Inductor
        d.add(el_a().down().label(ba_comp, loc='bottom'))
        d.add(elm.Ground())
        d.pop()
        el_c = elm.Capacitor if 'pF' in bc_comp else elm.Inductor
        d.add(el_c().right().label(bc_comp, loc='top'))
        d.add(elm.Line().right(d.unit / 2)) 
        d.push()
        el_b = elm.Capacitor if 'pF' in bb_comp else elm.Inductor
        d.add(el_b().down().label(bb_comp, loc='bottom'))
        d.add(elm.Ground())
        d.pop()
        d.add(elm.Resistor().right().label('$Z_L$\n' + f'{z_load.real:.1f} + {z_load.imag:.1f}j Ω', loc='bottom'))
    print(f"  Circuit diagram generated: {filename}")


# --- Network Calculation Functions ---

def calculate_l_section(frequency_hz, z_source, z_load):
    omega = 2 * np.pi * frequency_hz
    Rs, Xs = z_source.real, z_source.imag
    Rl, Xl = z_load.real, z_load.imag
    
    valid_solutions = [] 
    global_sol_counter = 1

    def solve_match(r_s, x_s, r_l, x_l):
        solutions = []
        D = (4 * (r_s**2) * (x_l**2)) - (4 * (r_s**2) * (r_l**2 + x_l**2)) + (4 * r_s * r_l * (r_s**2 + x_s**2))
        if D < 0: return solutions, "Discriminant < 0"
        sqrt_D = np.sqrt(D)
        denominator = 2 * r_s
        if abs(denominator) < 1e-9: return solutions, "Rs=0"
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

    print("\n--- L-Section Solutions ---")
    
    # Case 1: Shunt at Source
    sols1, _ = solve_match(Rs, Xs, Rl, Xl)
    if sols1:
        for sol in sols1:
            xa, xb = sol['X_a'], sol['X_b']
            shunt_str = get_component_string(xa, omega)
            series_str = get_component_string(xb, omega)
            type_a, val_a = get_numeric_component_value(xa, omega)
            type_b, val_b = get_numeric_component_value(xb, omega)

            if type_a and type_b:
                print(f"[{global_sol_counter}] Shunt-Series (Shunt@Source)")
                print(f"    Shunt: {shunt_str}, Series: {series_str}")
                draw_l_section(global_sol_counter, z_source, z_load, shunt_str, series_str, 'shunt_source')
                
                valid_solutions.append({
                    'id': global_sol_counter, 'type': 'L_ShuntSource',
                    'comps': [{'pos': 'shunt', 'type': type_a, 'val': val_a}, {'pos': 'series', 'type': type_b, 'val': val_b}]
                })
                global_sol_counter += 1

    # Case 2: Shunt at Load
    sols2, _ = solve_match(Rl, Xl, Rs, Xs)
    if sols2:
        for sol in sols2:
            xa, xb = sol['X_a'], sol['X_b'] 
            series_str = get_component_string(xb, omega)
            shunt_str = get_component_string(xa, omega)
            type_a, val_a = get_numeric_component_value(xa, omega) 
            type_b, val_b = get_numeric_component_value(xb, omega) 

            if type_a and type_b:
                print(f"[{global_sol_counter}] Series-Shunt (Shunt@Load)")
                print(f"    Series: {series_str}, Shunt: {shunt_str}")
                draw_l_section(global_sol_counter, z_source, z_load, shunt_str, series_str, 'shunt_load')

                valid_solutions.append({
                    'id': global_sol_counter, 'type': 'L_ShuntLoad',
                    'comps': [{'pos': 'series', 'type': type_b, 'val': val_b}, {'pos': 'shunt', 'type': type_a, 'val': val_a}]
                })
                global_sol_counter += 1
    return valid_solutions

def calculate_t_section(frequency_hz, z_source, z_load, q_max):
    omega = 2 * np.pi * frequency_hz
    Rs, Xs = z_source.real, z_source.imag
    Rl, Xl = z_load.real, z_load.imag
    valid_solutions = []
    global_sol_counter = 1
    topology = "standard" if Rl < Rs else "swapped"
    args = (Rs, Xs, Rl, Xl) if Rl < Rs else (Rl, Xl, Rs, Xs)
    solutions, error = _solve_t_pi_math(*args, q_max)

    if error or not solutions:
        print(f"No T-section solutions: {error}")
        return []

    print("\n--- T-Section Solutions ---")
    for sol in solutions:
        if topology == "standard": xa, xb, xc = sol['Xa'], sol['Xb'], sol['Xc']
        else: xa, xb, xc = sol['Xb'], sol['Xa'], sol['Xc']

        str_a = get_component_string(xa, omega)
        str_b = get_component_string(xb, omega)
        str_c = get_component_string(xc, omega)
        ta, va = get_numeric_component_value(xa, omega)
        tb, vb = get_numeric_component_value(xb, omega)
        tc, vc = get_numeric_component_value(xc, omega)

        if all([ta, tb, tc]):
            print(f"[{global_sol_counter}] T-Network")
            print(f"    Ser(S): {str_a}, Shu: {str_c}, Ser(L): {str_b}")
            draw_t_section(global_sol_counter, z_source, z_load, str_a, str_b, str_c)
            valid_solutions.append({
                'id': global_sol_counter, 'type': 'T_Section',
                'comps': [{'pos': 'series', 'type': ta, 'val': va}, {'pos': 'shunt', 'type': tc, 'val': vc}, {'pos': 'series', 'type': tb, 'val': vb}]
            })
            global_sol_counter += 1
    return valid_solutions

def calculate_pi_section(frequency_hz, z_source, z_load, q_max):
    omega = 2 * np.pi * frequency_hz
    y_source = 1 / z_source
    y_load = 1 / z_load
    Gs, Bs = y_source.real, y_source.imag
    Gl, Bl = y_load.real, y_load.imag
    valid_solutions = []
    global_sol_counter = 1
    topology = "standard" if Gl < Gs else "swapped"
    args = (Gs, Bs, Gl, Bl) if Gl < Gs else (Gl, Bl, Gs, Bs)
    solutions, error = _solve_t_pi_math(*args, q_max)

    if error or not solutions:
        print(f"No Pi-section solutions: {error}")
        return []

    print("\n--- Pi-Section Solutions ---")
    for sol in solutions:
        if topology == "standard": ba, bb, bc = sol['Xa'], sol['Xb'], sol['Xc']
        else: ba, bb, bc = sol['Xb'], sol['Xa'], sol['Xc']

        def b_to_x(b_val): return 1/b_val if abs(b_val) > 1e-12 else np.nan
        xa, xb, xc = b_to_x(ba), b_to_x(bb), b_to_x(bc)
        str_a = get_component_string(xa, omega)
        str_b = get_component_string(xb, omega)
        str_c = get_component_string(xc, omega)
        ta, va = get_numeric_component_value(xa, omega)
        tb, vb = get_numeric_component_value(xb, omega)
        tc, vc = get_numeric_component_value(xc, omega)

        if all([ta, tb, tc]):
            print(f"[{global_sol_counter}] Pi-Network")
            print(f"    Shu(S): {str_a}, Ser: {str_c}, Shu(L): {str_b}")
            draw_pi_section(global_sol_counter, z_source, z_load, str_a, str_b, str_c)
            valid_solutions.append({
                'id': global_sol_counter, 'type': 'Pi_Section',
                'comps': [{'pos': 'shunt', 'type': ta, 'val': va}, {'pos': 'series', 'type': tc, 'val': vc}, {'pos': 'shunt', 'type': tb, 'val': vb}]
            })
            global_sol_counter += 1
    return valid_solutions

# --- Plotting Logic (Corrected) ---

def plot_selected_solutions(solutions_list, f_center, z_s, z_l_complex):
    if not solutions_list:
        print("No solutions available to plot.")
        return

    print("\n" + "="*30 + "\n  PLOTTING SELECTION\n" + "="*30)
    print("Enter solution IDs (e.g., '1, 3') or 'all':")
    user_sel = input("Selection: ").strip().lower()
    
    selected_indices = []
    if user_sel == 'all':
        selected_indices = [s['id'] for s in solutions_list]
    else:
        try:
            parts = user_sel.split(',')
            for p in parts:
                selected_indices.append(int(p.strip()))
        except ValueError:
            print("Invalid selection format.")
            return

    to_plot = [s for s in solutions_list if s['id'] in selected_indices]
    if not to_plot: return

    # --- DETERMINE LOAD REACTANCE TYPE ---
    omega_center = 2 * np.pi * f_center
    load_reactance = z_l_complex.imag
    load_resistance = z_l_complex.real
    load_comp_type = None
    load_comp_val = 0.0
    
    if abs(load_reactance) > 1e-9:
        if load_reactance > 0:
            load_comp_type = 'L'; load_comp_val = load_reactance / omega_center
        else:
            load_comp_type = 'C'; load_comp_val = -1 / (load_reactance * omega_center)
    
    freqs = np.linspace(0.2 * f_center, 2.0 * f_center, 500)
    
    print(f"\nGenerating {len(to_plot)} separate plot windows... (They will appear simultaneously)")

    # --- LOOP THROUGH SOLUTIONS ---
    for sol in to_plot:
        # Create a NEW independent figure for each solution
        plt.figure(figsize=(8, 5)) 
        
        il_data = []
        for f in freqs:
            omega = 2 * np.pi * f
            # 1. Recalc Load
            current_zl_imag = 0.0
            if load_comp_type == 'L': current_zl_imag = omega * load_comp_val
            elif load_comp_type == 'C': current_zl_imag = -1 / (omega * load_comp_val)
            z_l_current = complex(load_resistance, current_zl_imag)
            z_s_current = z_s 
            
            # 2. Build Matrix
            abcd_total = np.eye(2, dtype=complex)
            for comp in sol['comps']:
                z_val = get_z_component(comp['type'], comp['val'], omega)
                if comp['pos'] == 'series': m_step = get_abcd_series(z_val)
                elif comp['pos'] == 'shunt': m_step = get_abcd_shunt(z_val)
                abcd_total = np.dot(abcd_total, m_step)
            
            il = calculate_insertion_loss_db(abcd_total, z_s_current, z_l_current)
            il_data.append(il)
            
        # Plot onto the specific figure created for this loop
        plt.plot(freqs / 1e6, il_data, label=f"Sol {sol['id']} ({sol['type']})", linewidth=2)
        plt.axvline(f_center / 1e6, color='k', linestyle='--', alpha=0.5, label='Center Freq')
        plt.title(f"Insertion Loss - Solution {sol['id']}")
        plt.xlabel("Frequency (MHz)")
        plt.ylabel("Insertion Loss (dB)")
        plt.legend()
        plt.grid(True, which='both', alpha=0.3)
        plt.tight_layout()
        
        # DO NOT call plt.show() here yet. 
        # If we call it here, the code pauses until you close window 1, then generates window 2.
    
    # Call show() ONCE at the very end to display all created figures at the same time.
    plt.show()

# --- Main ---

def main():
    print("=============================================")
    print(" Passive Matching Network Design Tool 📡")
    print("=============================================")
    print("\nSelect the matching network topology:")
    print("  1. L-Section")
    print("  2. π-Section (Pi-Section)")
    print("  3. T-Section")
    choice = input("Enter your choice (1-3): ")
    if choice not in ['1', '2', '3']: return

    print("\nPlease provide the following parameters:")
    frequency_mhz = get_float_input("Operating Frequency (in MHz): ")
    z_source = get_complex_input("Source Impedance (Z_S):")
    z_load = get_complex_input("Load Impedance (Z_L):")
    frequency_hz = frequency_mhz * 1e6
    generated_solutions = []

    if choice == '1':
        generated_solutions = calculate_l_section(frequency_hz, z_source, z_load)
    elif choice in ['2', '3']:
        q_s = abs(z_source.imag) / z_source.real if z_source.real > 1e-9 else 0
        q_l = abs(z_load.imag) / z_load.real if z_load.real > 1e-9 else 0
        min_q = max(q_s, q_l)
        print(f"Min required Q_max: {min_q:.2f}")
        q_max = get_float_input("Enter Maximum Nodal Q (Q_max): ")
        if q_max < min_q:
            print("Error: Q_max too low.")
            return
        if choice == '2':
            generated_solutions = calculate_pi_section(frequency_hz, z_source, z_load, q_max)
        else:
            generated_solutions = calculate_t_section(frequency_hz, z_source, z_load, q_max)

    if generated_solutions:
        plot_selected_solutions(generated_solutions, frequency_hz, z_source, z_load)

if __name__ == "__main__":
    main()