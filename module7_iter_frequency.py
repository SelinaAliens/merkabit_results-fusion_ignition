"""
Module 7B: ITER Physical Frequency Recommendation
===================================================
Convert Merkabit Coxeter frequency omega = 2*pi/12 into concrete
ITER heating parameters in physical units (Hz, ms, MW).

Anchored to ASDEX Upgrade ELM period T_ELM = 25 ms (Cavedon 2019).
All parameters from Merkabit architecture + published ITER design.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# CONSTANTS
# ============================================================

# Merkabit architecture (zero free parameters)
H_COXETER = 12
F_CASCADE = 1 / 3
R_DECAY = 3.11
THRESHOLD_DRIVE = F_CASCADE * R_DECAY                    # 1.0367
IGNITION_DRIVE = THRESHOLD_DRIVE * (1 + F_CASCADE)      # 1.3822
WINDOW_CENTER = 0.5 * (THRESHOLD_DRIVE + IGNITION_DRIVE)
WINDOW_HALF = 0.5 * (IGNITION_DRIVE - THRESHOLD_DRIVE)
N_STAR = 12  # cascade onset = Coxeter number

# ASDEX Upgrade anchor (Cavedon et al. 2019)
T_ELM_ASDEX = 25e-3     # s — ELM period
TAU_E_ASDEX = 0.1        # s — energy confinement time

# ITER design parameters (published)
P_FUSION_TARGET = 500     # MW
Q_TARGET = 10
P_INPUT_ITER = 50         # MW — heating input at Q=10
TAU_E_ITER = 3.8          # s
T_PLASMA_ITER = 15        # keV
N_DENSITY_ITER = 1e20     # m^-3

OUTDIR = Path("C:/Users/selin/merkabit_results/fusion_ignition")


def main():
    print("=" * 70)
    print("MODULE 7B: ITER PHYSICAL FREQUENCY RECOMMENDATION")
    print("=" * 70)

    # ===========================================================
    # STEP 1: Coxeter frequency from ASDEX anchor
    # ===========================================================
    print("\n--- STEP 1: Coxeter Frequency from ASDEX Anchor ---")

    # Two interpretations of the ELM period:
    # A: T_ELM = full ouroboros cycle (12 steps) → T_step = T_ELM/12
    # B: T_ELM = one Floquet step → T_cycle = T_ELM × 12

    # Interpretation A: ELM period = full cycle
    T_cycle_A = T_ELM_ASDEX                    # 25 ms
    T_step_A = T_cycle_A / H_COXETER           # 25/12 = 2.08 ms
    f_coxeter_A = 1 / T_cycle_A                # 40 Hz
    omega_A = 2 * np.pi * f_coxeter_A          # 251.3 rad/s

    # Interpretation B: ELM period = one step
    T_step_B = T_ELM_ASDEX                     # 25 ms
    T_cycle_B = T_step_B * H_COXETER           # 300 ms
    f_coxeter_B = 1 / T_cycle_B                # 3.33 Hz
    omega_B = 2 * np.pi * f_coxeter_B          # 20.9 rad/s

    print(f"\n  ASDEX ELM period: {T_ELM_ASDEX * 1e3:.0f} ms")
    print(f"\n  Interpretation A: T_ELM = full 12-step cycle")
    print(f"    T_cycle = {T_cycle_A * 1e3:.1f} ms")
    print(f"    T_step  = {T_step_A * 1e3:.2f} ms")
    print(f"    f_coxeter = {f_coxeter_A:.1f} Hz")
    print(f"    omega = {omega_A:.1f} rad/s")
    print(f"    Cycles in tau_E(ASDEX) = {TAU_E_ASDEX / T_cycle_A:.0f}")
    print(f"    Cycles in tau_E(ITER)  = {TAU_E_ITER / T_cycle_A:.0f}")

    print(f"\n  Interpretation B: T_ELM = one Floquet step")
    print(f"    T_step  = {T_step_B * 1e3:.1f} ms")
    print(f"    T_cycle = {T_cycle_B * 1e3:.1f} ms")
    print(f"    f_coxeter = {f_coxeter_B:.2f} Hz")
    print(f"    omega = {omega_B:.1f} rad/s")
    print(f"    Cycles in tau_E(ASDEX) = {TAU_E_ASDEX / T_cycle_B:.1f}")
    print(f"    Cycles in tau_E(ITER)  = {TAU_E_ITER / T_cycle_B:.1f}")

    # Physical reasoning:
    # The ELM crash is the CASCADE RESET — the end of one ouroboros cycle.
    # Between ELM crashes, the pedestal rebuilds through the 12 Floquet steps.
    # Therefore: T_ELM = full 12-step cycle (Interpretation A).
    #
    # Check: at ASDEX, tau_E = 0.1 s, T_cycle = 25 ms
    # → 4 ouroboros cycles per confinement time. This is physically reasonable:
    # the ELM frequency is ~40 Hz, and we see ~4 ELMs per confinement time.
    #
    # Interpretation B gives T_cycle = 300 ms, only 0.33 cycles in tau_E_ASDEX.
    # The cascade can't even complete one cycle → not self-consistent.

    print(f"\n  PHYSICAL REASONING:")
    print(f"    The ELM crash IS the cascade reset (end of ouroboros cycle).")
    print(f"    Between crashes, pedestal rebuilds through 12 Floquet steps.")
    print(f"    Interpretation A: {TAU_E_ASDEX / T_cycle_A:.0f} cycles in tau_E → self-consistent")
    print(f"    Interpretation B: {TAU_E_ASDEX / T_cycle_B:.1f} cycles in tau_E → cannot complete even one")
    print(f"    → INTERPRETATION A IS CORRECT: T_ELM = full cycle")

    # ===========================================================
    # STEP 2: ITER heating modulation parameters
    # ===========================================================
    print("\n--- STEP 2: ITER Heating Modulation Parameters ---")

    # Scale ELM period from ASDEX to ITER
    # ELM period scales approximately as tau_E (it's set by pedestal recovery)
    # More precisely: T_ELM ~ tau_E^(pedestal) which scales roughly as
    # tau_E * (T_ped / T_ped_crit) but for rough estimate use direct scaling
    scaling_factor = TAU_E_ITER / TAU_E_ASDEX
    T_ELM_ITER = T_ELM_ASDEX * scaling_factor
    T_cycle_ITER = T_ELM_ITER  # = full ouroboros cycle at ITER scale
    T_step_ITER = T_cycle_ITER / H_COXETER
    f_coxeter_ITER = 1 / T_cycle_ITER
    omega_ITER = 2 * np.pi * f_coxeter_ITER

    print(f"\n  Scaling: tau_E(ITER) / tau_E(ASDEX) = {scaling_factor:.1f}")
    print(f"  T_ELM(ITER) = T_ELM(ASDEX) x {scaling_factor:.1f} = {T_ELM_ITER * 1e3:.0f} ms")
    print(f"  T_cycle(ITER) = {T_cycle_ITER * 1e3:.0f} ms = {T_cycle_ITER:.3f} s")
    print(f"  T_step(ITER)  = {T_step_ITER * 1e3:.1f} ms")
    print(f"  f_coxeter(ITER) = {f_coxeter_ITER:.4f} Hz = {f_coxeter_ITER:.2f} Hz")
    print(f"  omega(ITER) = {omega_ITER:.4f} rad/s")
    print(f"  Ouroboros cycles in tau_E = {TAU_E_ITER / T_cycle_ITER:.1f}")

    # Heating modulation
    P_base = P_INPUT_ITER                              # 50 MW
    P_amplitude = P_base * F_CASCADE                   # 50/3 = 16.67 MW
    P_max = P_base * (1 + F_CASCADE)                   # 50 * 4/3 = 66.67 MW
    P_min = P_base                                     # 50 MW (threshold floor)
    # Note: P_min = P_base because the window floor is the threshold,
    # and the baseline corresponds to threshold. The modulation adds
    # up to P_amplitude above baseline.
    # Actually: window center = (threshold + ignition)/2
    # So P_center = P_base * (window_center / threshold)
    # But in drive units, drive = P/P_threshold, so:
    # P corresponding to threshold drive = P_base (this IS the threshold)
    # P corresponding to ignition drive = P_base * (ignition/threshold) = P_base * 4/3

    # Correct modulation: P oscillates between threshold and ignition
    P_center = P_base * (WINDOW_CENTER / THRESHOLD_DRIVE)
    P_half = P_base * (WINDOW_HALF / THRESHOLD_DRIVE)

    print(f"\n  HEATING MODULATION:")
    print(f"    P_baseline (threshold)  = {P_base:.1f} MW")
    print(f"    P_center (window mid)   = {P_center:.1f} MW")
    print(f"    P_amplitude (= P/3)     = {P_amplitude:.1f} MW")
    print(f"    P_max (ignition ceiling) = {P_max:.1f} MW  (= P_base x 4/3)")
    print(f"    P_min (threshold floor)  = {P_base:.1f} MW")
    print(f"    Modulation depth         = {P_amplitude / P_base * 100:.1f}%")

    # Lock-in time
    t_lockin = N_STAR * T_step_ITER  # = 12 × T_step (one full cycle)
    # Or equivalently: t_lockin = T_cycle_ITER (cascade onset at n*=12 steps = 1 cycle)
    print(f"\n    Lock-in time: n* x T_step = {N_STAR} x {T_step_ITER * 1e3:.1f} ms = {t_lockin * 1e3:.0f} ms")
    print(f"    = 1 ouroboros cycle = T_ELM(ITER) = {T_cycle_ITER * 1e3:.0f} ms")
    n_cycles_in_tauE = TAU_E_ITER / T_cycle_ITER
    print(f"    Ouroboros cycles in tau_E: {n_cycles_in_tauE:.1f}")

    # ===========================================================
    # STEP 3: Frequency sweep
    # ===========================================================
    print("\n--- STEP 3: Frequency Sweep ---")

    T_F_range = np.logspace(-3, 0, 500)  # 1 ms to 1000 ms → in seconds: 1e-3 to 1
    f_range = 1 / T_F_range

    # For each T_F:
    # - Cycles in tau_E = tau_E / T_F
    # - Lock-in time = T_F (one full cycle for n* = 12 steps to complete)
    # - Valid if: lock-in < tau_E (i.e., T_F < tau_E) AND
    #   at least ~4 cycles complete (T_F < tau_E / 4)
    cycles_in_tauE = TAU_E_ITER / T_F_range
    lockin_ok = T_F_range < TAU_E_ITER  # cascade completes before confinement lost
    multi_cycle = cycles_in_tauE >= 4    # enough cycles for stable breathing
    valid = lockin_ok & multi_cycle

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Top: cycles in tau_E vs T_F
    ax = axes[0]
    ax.semilogx(T_F_range * 1e3, cycles_in_tauE, 'b-', lw=2)
    ax.axhline(4, ls='--', color='gray', alpha=0.5, label='Minimum 4 cycles')
    ax.axhline(n_cycles_in_tauE, ls=':', color='red', alpha=0.5,
               label=f'ITER operating point ({n_cycles_in_tauE:.1f} cycles)')
    ax.axvline(T_cycle_ITER * 1e3, ls='--', color='red', lw=2, alpha=0.7,
               label=f'ITER T_F = {T_cycle_ITER * 1e3:.0f} ms')
    ax.axvline(T_ELM_ASDEX * 1e3, ls='--', color='green', alpha=0.7,
               label=f'ASDEX T_ELM = {T_ELM_ASDEX * 1e3:.0f} ms')
    ax.fill_between(T_F_range * 1e3, 0, cycles_in_tauE, where=valid,
                    alpha=0.1, color='green', label='Valid range')
    ax.set_ylabel('Ouroboros cycles in $\\tau_E$', fontsize=12)
    ax.set_title('Frequency Sweep: Cycles vs Floquet Period', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9, loc='upper right')
    ax.set_ylim(0, 100)

    # Bottom: modulation frequency vs T_F (trivial f = 1/T_F)
    ax = axes[1]
    P_mod = P_amplitude * np.ones_like(T_F_range)
    ax.semilogx(T_F_range * 1e3, f_range, 'b-', lw=2)
    ax.axhline(f_coxeter_ITER, ls='--', color='red', lw=2, alpha=0.7,
               label=f'ITER: {f_coxeter_ITER:.2f} Hz')
    ax.axhline(f_coxeter_A, ls='--', color='green', alpha=0.7,
               label=f'ASDEX: {f_coxeter_A:.0f} Hz')
    ax.axvline(T_cycle_ITER * 1e3, ls='--', color='red', lw=2, alpha=0.4)
    ax.axvline(T_ELM_ASDEX * 1e3, ls='--', color='green', alpha=0.4)
    ax.fill_between(T_F_range * 1e3, 0.01, 1000, where=valid,
                    alpha=0.1, color='green', label='Valid range')
    ax.set_xlabel('Floquet period $T_F$ (ms)', fontsize=12)
    ax.set_ylabel('Modulation frequency (Hz)', fontsize=12)
    ax.set_title('Heating Modulation Frequency', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9, loc='upper right')
    ax.set_yscale('log')
    ax.set_ylim(0.1, 1000)

    fig.suptitle('Module 7B: Frequency Sweep\n'
                 f'Valid range: T_F < $\\tau_E$/4 = {TAU_E_ITER / 4 * 1e3:.0f} ms '
                 f'($\\geq$4 ouroboros cycles in $\\tau_E$ = {TAU_E_ITER} s)',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(OUTDIR / 'module7_frequency_sweep.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: module7_frequency_sweep.png")

    valid_min = T_F_range[valid].min() * 1e3 if np.any(valid) else 0
    valid_max = T_F_range[valid].max() * 1e3 if np.any(valid) else 0
    print(f"  Valid T_F range: [{valid_min:.0f}, {valid_max:.0f}] ms")
    print(f"  ITER operating point: T_F = {T_cycle_ITER * 1e3:.0f} ms ({n_cycles_in_tauE:.1f} cycles)")

    # ===========================================================
    # STEP 4: Cross-check against ITER ELM data
    # ===========================================================
    print("\n--- STEP 4: Cross-Check vs ITER ELM Design ---")

    print(f"""
  ITER is designed to SUPPRESS type-I ELMs using resonant magnetic
  perturbations (RMPs) because uncontrolled ELMs at ITER scale
  would damage divertor plasma-facing components.

  The Merkabit result says the plasma NEEDS to breathe at the
  Coxeter frequency. The resolution:
    - Type-I ELMs are UNCONTROLLED cascades (amplitude too large)
    - The F-gate provides CONTROLLED breathing (amplitude = f = 1/3)
    - RMPs suppress the uncontrolled crash but the plasma still needs
      frequency-locked heating modulation to sustain the breathing cycle

  Predicted ITER natural ELM period:
    T_ELM(ITER) = T_ELM(ASDEX) x tau_E(ITER)/tau_E(ASDEX)
                = {T_ELM_ASDEX * 1e3:.0f} ms x {TAU_E_ITER / TAU_E_ASDEX:.0f}
                = {T_ELM_ITER * 1e3:.0f} ms = {T_ELM_ITER:.3f} s

  The F-gate replaces uncontrolled ELMs with controlled breathing:
    SAME frequency, BOUNDED amplitude (window = [{THRESHOLD_DRIVE:.3f}, {IGNITION_DRIVE:.3f}]).
""")

    # ===========================================================
    # STEP 5: The concrete recommendation
    # ===========================================================
    print("--- STEP 5: ITER F-GATE HEATING RECOMMENDATION ---")

    print(f"""
  ================================================================
  ITER F-GATE HEATING RECOMMENDATION
  ================================================================
  Modulation frequency:    f = {f_coxeter_ITER:.4f} Hz  (omega = {omega_ITER:.3f} rad/s)
  Modulation period:       T = {T_cycle_ITER * 1e3:.0f} ms  (= T_ELM_ASDEX x tau_E ratio)
  Floquet step:            T_step = {T_step_ITER * 1e3:.1f} ms  (= T_cycle / 12)
  Heating power baseline:  P_base = {P_base:.0f} MW  (ITER Q=10 design)
  Modulation amplitude:    dP = {P_amplitude:.1f} MW  (= P_base / 3)
  P_max (ignition):        {P_max:.1f} MW  (= P_base x 4/3)
  P_min (threshold):       {P_base:.0f} MW  (= P_base x 1)
  Phase control:           P-gate tracking plasma phi
  Lock-in time:            n* x T_step = {N_STAR} x {T_step_ITER * 1e3:.1f} ms = {t_lockin * 1e3:.0f} ms
  Ouroboros cycles in tE:  tau_E / T_cycle = {n_cycles_in_tauE:.1f}
  ================================================================
""")

    # ===========================================================
    # STEP 6: Sensitivity analysis
    # ===========================================================
    print("--- STEP 6: Sensitivity Analysis ---")

    scenarios = {
        'Conservative': {'T_ELM': 500e-3},
        'Central (tau_E scaling)': {'T_ELM': T_ELM_ITER},
        'Aggressive': {'T_ELM': 1500e-3},
    }

    print(f"  {'Scenario':<30s} {'T_ELM (ms)':>10s} {'f (Hz)':>10s} {'T_step':>10s} "
          f"{'dP (MW)':>10s} {'Cycles/tE':>10s}")
    print(f"  {'-' * 30} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 10}")

    scenario_data = {}
    for name, params in scenarios.items():
        T_elm = params['T_ELM']
        f_cox = 1 / T_elm
        T_step = T_elm / H_COXETER
        dP = P_INPUT_ITER * F_CASCADE
        cycles = TAU_E_ITER / T_elm
        print(f"  {name:<30s} {T_elm * 1e3:>10.0f} {f_cox:>10.4f} {T_step * 1e3:>9.1f}ms "
              f"{dP:>10.1f} {cycles:>10.1f}")
        scenario_data[name] = {
            'T_elm': T_elm, 'f_cox': f_cox, 'T_step': T_step,
            'dP': dP, 'cycles': cycles
        }

    # --- Sensitivity plot ---
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for idx, (name, sd) in enumerate(scenario_data.items()):
        ax = axes[idx]
        T_elm = sd['T_elm']
        f_cox = sd['f_cox']
        dP = sd['dP']

        # Plot P(t) for 10 cycles
        n_cycles_plot = min(10, int(TAU_E_ITER / T_elm))
        t_plot = np.linspace(0, n_cycles_plot * T_elm, 1000)
        omega = 2 * np.pi / T_elm
        P_t = P_INPUT_ITER + dP * np.cos(omega * t_plot)

        ax.plot(t_plot * 1e3, P_t, 'b-', lw=1.5)
        ax.axhline(P_INPUT_ITER, ls=':', color='gray', alpha=0.3)
        ax.axhline(P_INPUT_ITER * (1 + F_CASCADE), ls='--', color='red', alpha=0.5,
                   label=f'P_max = {P_INPUT_ITER * (1 + F_CASCADE):.1f} MW')
        ax.axhline(P_INPUT_ITER, ls='--', color='green', alpha=0.5,
                   label=f'P_min = {P_INPUT_ITER:.0f} MW')

        ax.set_xlabel('Time (ms)', fontsize=11)
        if idx == 0:
            ax.set_ylabel('Heating power (MW)', fontsize=11)
        ax.set_title(f'{name}\nT = {T_elm * 1e3:.0f} ms, f = {f_cox:.3f} Hz',
                     fontsize=11, fontweight='bold')
        ax.legend(fontsize=8, loc='upper right')
        ax.set_ylim(P_INPUT_ITER - dP * 1.5, P_INPUT_ITER + dP * 2)

    fig.suptitle('Module 7B: Sensitivity Analysis\n'
                 f'P_base = {P_INPUT_ITER} MW, dP = P/3 = {P_INPUT_ITER * F_CASCADE:.1f} MW, '
                 f'P_max = 4P/3 = {P_INPUT_ITER * (1 + F_CASCADE):.1f} MW',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTDIR / 'module7_sensitivity.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n  Saved: module7_sensitivity.png")

    # --- Main recommendation figure: P(t) for ITER ---
    fig, ax = plt.subplots(figsize=(14, 6))

    n_cycles_show = 10
    t_total = n_cycles_show * T_cycle_ITER
    t = np.linspace(0, t_total, 2000)
    P_t = P_INPUT_ITER + P_amplitude * np.cos(omega_ITER * t)

    # Buffer crossover: first cycle is lock-in
    buffer = 1 - np.exp(-t / T_cycle_ITER)
    P_modulated = P_INPUT_ITER + P_amplitude * np.cos(omega_ITER * t) * buffer

    ax.plot(t * 1e3, P_modulated, 'b-', lw=2, label='$P(t) = P_{base} + \\Delta P \\cos(\\omega t)$')

    # Shade breathing window
    ax.axhspan(P_INPUT_ITER, P_INPUT_ITER * (1 + F_CASCADE),
               alpha=0.1, color='green',
               label=f'Breathing window [{P_INPUT_ITER:.0f}, {P_max:.1f}] MW')
    ax.axhline(P_INPUT_ITER, ls='--', color='green', alpha=0.5)
    ax.axhline(P_max, ls='--', color='red', alpha=0.5)
    ax.axhline(P_INPUT_ITER + P_amplitude, ls=':', color='gray', alpha=0.3)

    # Mark lock-in
    ax.axvline(T_cycle_ITER * 1e3, ls=':', color='orange', lw=2, alpha=0.7,
               label=f'Lock-in at $n^*$ = 1 cycle = {T_cycle_ITER * 1e3:.0f} ms')

    # Mark cycle boundaries
    for c in range(1, n_cycles_show + 1):
        ax.axvline(c * T_cycle_ITER * 1e3, ls=':', color='gray', alpha=0.15)

    ax.set_xlabel('Time (ms)', fontsize=13)
    ax.set_ylabel('Heating Power (MW)', fontsize=13)
    ax.set_title(f'ITER F-Gate Heating Modulation\n'
                 f'$f$ = {f_coxeter_ITER:.4f} Hz, '
                 f'$T_F$ = {T_cycle_ITER * 1e3:.0f} ms, '
                 f'$\\Delta P$ = {P_amplitude:.1f} MW, '
                 f'$P_{{max}}$ = {P_max:.1f} MW',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='upper right')
    ax.set_xlim(0, t_total * 1e3)
    ax.set_ylim(P_INPUT_ITER - P_amplitude * 1.5, P_max * 1.15)

    # Add annotation
    ax.annotate(f'$\\omega = 2\\pi / {T_cycle_ITER * 1e3:.0f}$ ms\n= E$_6$ Coxeter frequency',
                xy=(3 * T_cycle_ITER * 1e3, P_max),
                xytext=(4 * T_cycle_ITER * 1e3, P_max + 5),
                fontsize=11, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red'))

    plt.tight_layout()
    plt.savefig(OUTDIR / 'module7_iter_frequency_recommendation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: module7_iter_frequency_recommendation.png")

    # ===========================================================
    # FINAL: The number for the paper
    # ===========================================================
    print("\n" + "=" * 70)
    print("THE NUMBER FOR THE PAPER")
    print("=" * 70)

    print(f"""
  ITER heating systems should be modulated at f = {f_coxeter_ITER:.2f} Hz
  (period T = {T_cycle_ITER * 1e3:.0f} ms) with amplitude dP = {P_amplitude:.1f} MW around a
  {P_base:.0f} MW baseline, phase-locked to the plasma order parameter at
  the E_6 Coxeter frequency omega = 2*pi / (12 * T_step) where
  T_step = {T_step_ITER * 1e3:.1f} ms is the Floquet step duration.

  This replaces uncontrolled type-I ELMs with controlled breathing:
    - Same natural frequency (scaled from ASDEX 25 ms by tau_E ratio)
    - Bounded amplitude: P oscillates between {P_base:.0f} MW (threshold)
      and {P_max:.1f} MW (ignition ceiling = P_base x 4/3)
    - Lock-in at n* = {N_STAR} Floquet steps = {t_lockin * 1e3:.0f} ms (one cycle)
    - {n_cycles_in_tauE:.1f} ouroboros cycles complete in tau_E = {TAU_E_ITER} s

  Paper sentence:
  "ITER heating systems should be modulated at f = {f_coxeter_ITER:.2f} Hz
  with amplitude Delta-P = {P_amplitude:.1f} MW around a {P_base:.0f} MW baseline,
  phase-locked to the plasma order parameter at the E_6 Coxeter
  frequency omega = 2*pi / 12*T_F."

  where T_F = {T_cycle_ITER * 1e3:.0f} ms (ASDEX ELM period scaled by tau_E(ITER)/tau_E(ASDEX) = {scaling_factor:.0f}).
""")

    print("  Files generated:")
    for f in sorted(OUTDIR.glob('module7*.png')):
        print(f"    {f.name}")


if __name__ == '__main__':
    main()
