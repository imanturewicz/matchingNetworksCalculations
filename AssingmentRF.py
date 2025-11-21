import numpy as np
import matplotlib
# We DO NOT use matplotlib.use('Agg') because we want plt.show() to work interactively
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
    if np.isnan(reactance) or abs(omega) < 1e-12: return "N/A"
    if reactance > 0:
        return f"{(reactance/omega)*1e9:.3f} nH (L)"
    elif reactance < 0:
        return f"{(-1/(omega*reactance))*1e12:.3f} pF (C)"
    else:
        return "Short"

def get_numeric_component_value(reactance, omega):
    """Returns a tuple: (Component Type 'L'/'C', Value in Henry/Farad)."""
    if np.isnan(reactance) or abs(omega) < 1e-12: return None, 0.0
    if reactance > 0: return 'L', reactance / omega
    elif reactance < 0: return 'C', -1 / (omega * reactance)
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
    """Calculates S21 (Insertion Loss) in dB."""
    A, B, C, D = abcd_matrix[0, 0], abcd_matrix[0, 1], abcd_matrix[1, 0], abcd_matrix[1, 1]
    numerator = A * Zl + B + C * Zs * Zl + D * Zs
    denominator = 2 * np.sqrt(Zs.real * Zl.real)
    if denominator == 0: denominator = 1e-12
    ratio = abs(numerator) / denominator
    if ratio == 0: return -100
    # Returns negative dB (S21)
    return -20 * np.log10(ratio)

def calculate_return_loss_db(abcd_matrix, Zs, Zl):
    """Calculates S11 (Return Loss) in dB."""
    A, B, C, D = abcd_matrix[0, 0], abcd_matrix[0, 1], abcd_matrix[1, 0], abcd_matrix[1, 1]
    
    # 1. Calculate Input Impedance (Zin)
    numerator_zin = A * Zl + B
    denominator_zin = C * Zl + D
    
    if abs(denominator_zin) < 1e-12: Zin = 1e12
    else: Zin = numerator_zin / denominator_zin
    
    # 2. Calculate Reflection Coefficient (Gamma)
    denominator_gamma = Zin + Zs
    if abs(denominator_gamma) < 1e-12: gamma = 1.0
    else: gamma = (Zin - Zs) / denominator_gamma
    
    mag_gamma = abs(gamma)
    
    if mag_gamma < 1e-9: return -100.0
    return 20 * np.log10(mag_gamma)

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

# --- Drawing Helper (Draws on the provided Axis) ---
def draw_circuit_on_axis(ax, sol, zs, zl, omega):
    d = schemdraw.Drawing(canvas=ax, show=False)
    d.config(unit=3)
    
    def get_elm(comp_data):
        ctype = comp_data['type']
        cval = comp_data['val']
        lbl = get_component_string(get_z_component(ctype, cval, omega).imag, omega)
        return (elm.Capacitor if ctype=='C' else elm.Inductor, lbl)

    d.push()
    d.add(elm.Ground())
    d.pop()
    d.add(elm.SourceV().up().label(f'$Z_S$\n{zs.real:.0f}+{zs.imag:.0f}j', loc='bottom'))
    
    comps = sol['comps']
    stype = sol['type']

    if stype == 'L_ShuntSource':
        e1, l1 = get_elm(comps[0])
        e2, l2 = get_elm(comps[1])
        d.add(elm.Line().right(d.unit*1.5))
        d.push()
        d.add(e1().down().label(l1, loc='bottom'))
        d.add(elm.Ground())
        d.pop()
        d.add(e2().right().label(l2, loc='top'))
        d.add(elm.Line().right(d.unit*0.5))

    elif stype == 'L_ShuntLoad':
        e1, l1 = get_elm(comps[0])
        e2, l2 = get_elm(comps[1])
        d.add(e1().right(d.unit*1.5).label(l1, loc='top'))
        d.push()
        d.add(e2().down().label(l2, loc='bottom'))
        d.add(elm.Ground())
        d.pop()
        d.add(elm.Line().right(d.unit*0.5))

    elif stype == 'T_Section':
        e1, l1 = get_elm(comps[0])
        e2, l2 = get_elm(comps[1])
        e3, l3 = get_elm(comps[2])
        d.add(e1().right(d.unit*1.5).label(l1, loc='top'))
        d.push()
        d.add(e2().down().label(l2, loc='bottom'))
        d.add(elm.Ground())
        d.pop()
        d.add(e3().right().label(l3, loc='top'))
        d.add(elm.Line().right(d.unit*0.5))

    elif stype == 'Pi_Section':
        e1, l1 = get_elm(comps[0])
        e2, l2 = get_elm(comps[1])
        e3, l3 = get_elm(comps[2])
        d.add(elm.Line().right(d.unit*1.5))
        d.push()
        d.add(e1().down().label(l1, loc='bottom'))
        d.add(elm.Ground())
        d.pop()
        d.add(e2().right().label(l2, loc='top'))
        d.add(elm.Line().right(d.unit*0.5))
        d.push()
        d.add(e3().down().label(l3, loc='bottom'))
        d.add(elm.Ground())
        d.pop()

    d.add(elm.Resistor().right().label(f'$Z_L$\n{zl.real:.0f}+{zl.imag:.0f}j', loc='bottom'))
    d.add(elm.Ground())
    d.draw() 

# --- Calculation Functions ---
def calculate_l_section(frequency_hz, z_source, z_load):
    omega = 2 * np.pi * frequency_hz
    Rs, Xs = z_source.real, z_source.imag
    Rl, Xl = z_load.real, z_load.imag
    sols = [] 
    id_ctr = 1

    def solve_match(r_s, x_s, r_l, x_l):
        solutions = []
        D = (4 * (r_s**2) * (x_l**2)) - (4 * (r_s**2) * (r_l**2 + x_l**2)) + (4 * r_s * r_l * (r_s**2 + x_s**2))
        if D < 0: return solutions
        sqrt_D = np.sqrt(D)
        denominator = 2 * r_s
        if abs(denominator) < 1e-9: return solutions
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
        return solutions

    print("\n--- L-Section Solutions ---")
    for s in solve_match(Rs, Xs, Rl, Xl):
        ta, va = get_numeric_component_value(s['X_a'], omega)
        tb, vb = get_numeric_component_value(s['X_b'], omega)
        if ta and tb:
            print(f"[{id_ctr}] L-Section (Shunt at Source)")
            print(f"    Shunt: {get_component_string(s['X_a'], omega)}, Series: {get_component_string(s['X_b'], omega)}")
            sols.append({'id': id_ctr, 'type': 'L_ShuntSource', 
                         'comps': [{'pos': 'shunt', 'type': ta, 'val': va}, 
                                   {'pos': 'series', 'type': tb, 'val': vb}]})
            id_ctr += 1

    for s in solve_match(Rl, Xl, Rs, Xs):
        ta, va = get_numeric_component_value(s['X_a'], omega) 
        tb, vb = get_numeric_component_value(s['X_b'], omega) 
        if ta and tb:
            print(f"[{id_ctr}] L-Section (Shunt at Load)")
            print(f"    Series: {get_component_string(s['X_b'], omega)}, Shunt: {get_component_string(s['X_a'], omega)}")
            sols.append({'id': id_ctr, 'type': 'L_ShuntLoad', 
                         'comps': [{'pos': 'series', 'type': tb, 'val': vb},
                                   {'pos': 'shunt', 'type': ta, 'val': va}]})
            id_ctr += 1
    return sols

def calculate_t_section(frequency_hz, z_source, z_load, q_max):
    omega = 2 * np.pi * frequency_hz
    Rs, Xs = z_source.real, z_source.imag
    Rl, Xl = z_load.real, z_load.imag
    sols = []
    id_ctr = 1
    topology = "standard" if Rl < Rs else "swapped"
    args = (Rs, Xs, Rl, Xl) if Rl < Rs else (Rl, Xl, Rs, Xs)
    math_sols, error = _solve_t_pi_math(*args, q_max)

    if not math_sols:
        print(f"No T-section solutions: {error}")
        return []

    print("\n--- T-Section Solutions ---")
    for s in math_sols:
        if topology == "standard": xa, xb, xc = s['Xa'], s['Xb'], s['Xc']
        else: xa, xb, xc = s['Xb'], s['Xa'], s['Xc']

        ta, va = get_numeric_component_value(xa, omega)
        tb, vb = get_numeric_component_value(xb, omega)
        tc, vc = get_numeric_component_value(xc, omega)

        if all([ta, tb, tc]):
            print(f"[{id_ctr}] T-Network")
            print(f"    Ser(S): {get_component_string(xa, omega)}, Shu: {get_component_string(xc, omega)}, Ser(L): {get_component_string(xb, omega)}")
            sols.append({
                'id': id_ctr, 'type': 'T_Section',
                'comps': [{'pos': 'series', 'type': ta, 'val': va}, 
                          {'pos': 'shunt', 'type': tc, 'val': vc}, 
                          {'pos': 'series', 'type': tb, 'val': vb}]
            })
            id_ctr += 1
    return sols

def calculate_pi_section(frequency_hz, z_source, z_load, q_max):
    omega = 2 * np.pi * frequency_hz
    y_source = 1 / z_source
    y_load = 1 / z_load
    Gs, Bs = y_source.real, y_source.imag
    Gl, Bl = y_load.real, y_load.imag
    sols = []
    id_ctr = 1
    topology = "standard" if Gl < Gs else "swapped"
    args = (Gs, Bs, Gl, Bl) if Gl < Gs else (Gl, Bl, Gs, Bs)
    math_sols, error = _solve_t_pi_math(*args, q_max)

    if not math_sols:
        print(f"No Pi-section solutions: {error}")
        return []

    print("\n--- Pi-Section Solutions ---")
    for s in math_sols:
        if topology == "standard": ba, bb, bc = s['Xa'], s['Xb'], s['Xc']
        else: ba, bb, bc = s['Xb'], s['Xa'], s['Xc']

        def b_to_x(b_val): return 1/b_val if abs(b_val) > 1e-12 else np.nan
        xa, xb, xc = b_to_x(ba), b_to_x(bb), b_to_x(bc)

        ta, va = get_numeric_component_value(xa, omega)
        tb, vb = get_numeric_component_value(xb, omega)
        tc, vc = get_numeric_component_value(xc, omega)

        if all([ta, tb, tc]):
            print(f"[{id_ctr}] Pi-Network")
            print(f"    Shu(S): {get_component_string(xa, omega)}, Ser: {get_component_string(xc, omega)}, Shu(L): {get_component_string(xb, omega)}")
            sols.append({
                'id': id_ctr, 'type': 'Pi_Section',
                'comps': [{'pos': 'shunt', 'type': ta, 'val': va}, 
                          {'pos': 'series', 'type': tc, 'val': vc}, 
                          {'pos': 'shunt', 'type': tb, 'val': vb}]
            })
            id_ctr += 1
    return sols

# --- Plotting Logic (Updated for 1x3 Side-by-Side) ---
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

    # Load Setup
    omega_center = 2 * np.pi * f_center
    load_reactance = z_l_complex.imag
    load_resistance = z_l_complex.real
    load_comp_type = None
    load_comp_val = 0.0
    if abs(load_reactance) > 1e-9:
        if load_reactance > 0: load_comp_type = 'L'; load_comp_val = load_reactance / omega_center
        else: load_comp_type = 'C'; load_comp_val = -1 / (load_reactance * omega_center)
    
    freqs = np.linspace(0.2 * f_center, 2.0 * f_center, 500)
    
    print(f"\nGenerating {len(to_plot)} combined windows... (Simultaneous display)")

    # 1. ENABLE INTERACTIVE MODE
    plt.ion()

    # --- LOOP THROUGH SOLUTIONS ---
    for sol in to_plot:
        # CHANGED: 1 row, 3 cols. WIDE figure (18, 6)
        fig, (ax_schem, ax_il, ax_rl) = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f"Solution {sol['id']}: {sol['type']}", fontsize=16, weight='bold')
        
        # --- LEFT: SCHEMATIC ---
        draw_circuit_on_axis(ax_schem, sol, z_s, z_l_complex, 2*np.pi*f_center)
        ax_schem.set_axis_off()

        # --- DATA CALCULATION ---
        il_data = []
        rl_data = [] # Return Loss Data
        
        for f in freqs:
            omega = 2 * np.pi * f
            current_zl_imag = 0.0
            if load_comp_type == 'L': current_zl_imag = omega * load_comp_val
            elif load_comp_type == 'C': current_zl_imag = -1 / (omega * load_comp_val)
            z_l_current = complex(load_resistance, current_zl_imag)
            
            abcd_total = np.eye(2, dtype=complex)
            for comp in sol['comps']:
                z_val = get_z_component(comp['type'], comp['val'], omega)
                if comp['pos'] == 'series': m_step = get_abcd_series(z_val)
                elif comp['pos'] == 'shunt': m_step = get_abcd_shunt(z_val)
                abcd_total = np.dot(abcd_total, m_step)
            
            # Calculate both
            il_data.append(calculate_insertion_loss_db(abcd_total, z_s, z_l_current))
            rl_data.append(calculate_return_loss_db(abcd_total, z_s, z_l_current))
        
        # --- MIDDLE: INSERTION LOSS ---
        ax_il.plot(freqs / 1e6, il_data, linewidth=2, color='tab:blue', label='S21 (IL)')
        ax_il.axvline(f_center / 1e6, color='r', linestyle='--', alpha=0.7, label='Center Freq')
        ax_il.set_title("Insertion Loss (S21)", fontsize=12)
        ax_il.set_xlabel("Frequency (MHz)")
        ax_il.set_ylabel("Magnitude (dB)")
        ax_il.grid(True, which='both', alpha=0.3)
        ax_il.legend(loc='lower right')

        # --- RIGHT: RETURN LOSS ---
        ax_rl.plot(freqs / 1e6, rl_data, linewidth=2, color='tab:orange', label='S11 (RL)')
        ax_rl.axvline(f_center / 1e6, color='r', linestyle='--', alpha=0.7, label='Center Freq')
        ax_rl.axhline(-10, color='k', linestyle=':', alpha=0.5, label='-10dB Limit')
        ax_rl.set_title("Return Loss (S11)", fontsize=12)
        ax_rl.set_xlabel("Frequency (MHz)")
        ax_rl.set_ylabel("Magnitude (dB)")
        ax_rl.grid(True, which='both', alpha=0.3)
        ax_rl.legend(loc='lower right')
        
        # Adjust layout for side-by-side
        plt.subplots_adjust(wspace=0.3, top=0.85, bottom=0.15, left=0.05, right=0.95)
        
        # Show non-blockingly
        fig.show() 

    # 2. DISABLE INTERACTIVE MODE AND BLOCK
    plt.ioff()
    print("All windows generated. Close them to exit.")
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
        min_required_q = max(q_s, q_l)
        print(f"\nMin required Q_max (to absorb Zs/Zl): {min_required_q:.2f}")
        q_max = 0.0

        while True: 
            print("\nHow do you want to specify the network Q?")
            print("  1. Maximum Nodal Q (Q_max)")
            print("  2. Total Network Q (Q_tot)")
            print("  3. Bandwidth (BW) in MHz")
            q_choice = input("Enter your choice (1-3): ")

            if q_choice == '1':
                q_max = get_float_input("Enter Maximum Nodal Quality Factor (Q_max): ")
            elif q_choice == '2':
                q_tot = get_float_input("Enter Total Quality Factor (Q_tot): ")
                q_max = q_tot * 2
                print(f"-> Calculated Q_max = {q_tot} * 2 = {q_max:.2f}")
            elif q_choice == '3':
                bw_mhz = get_float_input("Enter Desired Bandwidth (in MHz): ")
                if bw_mhz <= 0:
                    print("Error: Bandwidth must be positive.")
                    continue
                q_tot = frequency_mhz / bw_mhz
                q_max = q_tot * 2
                print(f"-> Calculated Q_tot = {frequency_mhz}/{bw_mhz} = {q_tot:.2f}")
                print(f"-> Calculated Q_max = {q_tot:.2f} * 2 = {q_max:.2f}")
            else:
                print("Invalid choice.")
                continue

            if q_max < min_required_q:
                print(f"Error: Q_max must be >= {min_required_q:.2f}")
            else:
                break

        if choice == '2':
            generated_solutions = calculate_pi_section(frequency_hz, z_source, z_load, q_max)
        else:
            generated_solutions = calculate_t_section(frequency_hz, z_source, z_load, q_max)

    if generated_solutions:
        plot_selected_solutions(generated_solutions, frequency_hz, z_source, z_load)

if __name__ == "__main__":
    main()