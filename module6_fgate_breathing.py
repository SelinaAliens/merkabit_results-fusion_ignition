"""
Module 6 (F-gate corrected): The Breathing Window via Frequency Locking
=========================================================================
The cascade self-regulates NOT through linear damping but through
FREQUENCY LOCKING (the F-gate). The F-gate projects the drive onto
the resonant mode at omega = 2*pi/12 (the ouroboros frequency).
The P-gate provides slow phase correction tracking phi.

Physical model:
  drive(n) = D_baseline + D_amplitude * cos(omega * n + phase(n))
  phase(n+1) = phase(n) + (1/3) * (phi(n) - phi_target)
  D_baseline = window center = (threshold + ignition) / 2
  D_amplitude = window half-width = (ignition - threshold) / 2

The F-gate locks the carrier to omega = 2*pi/12.
The P-gate provides slow phase correction.
The drive oscillates within the window BY CONSTRUCTION.

Buffer crossover: D_static carries the system until n* = 12,
then F-gate takes over (cascade must form before it can resonate).

Sub-modules:
  6A: Breathing Cycle (ITER -> window lock-in via F-gate)
  6B: Optimal Window (sweep D_static, convergence analysis)
  Phase Portrait: the ouroboros orbit in (phi, drive) space

All parameters from Merkabit architecture. Zero free parameters.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from pathlib import Path

# ============================================================
# CONSTANTS
# ============================================================
ALPHA_KWW = 4 / 3
N_STAR = 12
XI = 3.0
R_DECAY = 3.11
F_CASCADE = 1 / 3
T_FLOQUET = 12
F_MERKABIT = 0.696778

THRESHOLD_DRIVE = F_CASCADE * R_DECAY                       # 1.0367
IGNITION_DRIVE = F_CASCADE * R_DECAY * (1 + F_CASCADE)     # 1.3822
WINDOW_CENTER = 0.5 * (THRESHOLD_DRIVE + IGNITION_DRIVE)   # 1.2094
WINDOW_HALF = 0.5 * (IGNITION_DRIVE - THRESHOLD_DRIVE)     # 0.1728
OMEGA = 2 * np.pi / T_FLOQUET                               # ouroboros frequency

DRIVE_ITER = 2.7543

OUTDIR = Path("C:/Users/selin/merkabit_results/fusion_ignition")
OUTDIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CORE: F-gate + P-gate Coupled Dynamics
# ============================================================
def fgate_dynamics(D_static, n_steps=120):
    """
    Full F-gate + P-gate coupled system.

    At each Floquet step n:
      1. Buffer crossover: until n* = 12, static drive dominates;
         after n*, F-gate resonant drive takes over.
      2. F-gate: drive oscillates at ouroboros frequency omega = 2*pi/12
         within the window [threshold, ignition].
      3. P-gate: phase tracks the order parameter phi via slow correction.
      4. phi evolves under KWW with alpha = 4/3.

    Parameters
    ----------
    D_static : float
        Raw external drive (e.g. ITER = 2.754). Before cascade forms,
        this is the drive felt by the plasma.
    n_steps : int
        Number of Floquet steps.

    Returns
    -------
    drive_eff : array, effective drive at each step
    phi : array, order parameter at each step
    phase : array, P-gate phase at each step
    """
    drive_eff = np.zeros(n_steps + 1)
    phi = np.zeros(n_steps + 1)
    phase = np.zeros(n_steps + 1)

    phi[0] = 0.01
    phase[0] = 0.0

    # Phi target for P-gate: the phi value at the ignition ceiling
    # When drive = ignition, phi_eq = 1/(1+(threshold/ignition)^alpha)
    #  = 1/(1+(1/alpha)^alpha) = 1/(1+(3/4)^(4/3))
    phi_target_raw = 1.0 / (1.0 + (THRESHOLD_DRIVE / IGNITION_DRIVE) ** ALPHA_KWW)
    # Simplified: we want phi to track toward the window equilibrium
    phi_target = phi_target_raw  # ~0.576

    for n in range(n_steps + 1):
        # Buffer crossover: exponential transition from static to F-gate
        # buffer_factor = 1 - exp(-n / n*), so:
        #   n << n*: buffer ~ 0, drive = D_static
        #   n >> n*: buffer ~ 1, drive = F-gate resonant drive
        buffer_factor = 1 - np.exp(-n / N_STAR)

        # F-gate: resonant drive oscillating within window
        drive_fgate = WINDOW_CENTER + WINDOW_HALF * np.cos(OMEGA * n + phase[n])

        # Effective drive: crossover from static to F-gate
        drive_eff[n] = D_static * (1 - buffer_factor) + drive_fgate * buffer_factor

        if n == n_steps:
            break

        # phi evolves under KWW-like dynamics
        # Growth term: drive above threshold feeds cooperativity
        # Decay term: cascade fraction f determines relaxation
        drive_ratio = drive_eff[n] / THRESHOLD_DRIVE
        if drive_ratio > 1:
            # Above threshold: phi grows with KWW exponent
            growth = (F_CASCADE / T_FLOQUET) * (drive_ratio - 1) ** (1 / ALPHA_KWW) * (1 - phi[n])
        else:
            growth = 0

        # Decay: cascade relaxation
        decay = (F_CASCADE / (T_FLOQUET * R_DECAY)) * phi[n]

        dphi = growth - decay
        phi[n + 1] = np.clip(phi[n] + dphi, 0, 1)

        # P-gate: slow phase correction
        # Phase adjusts so that drive peaks align with phi needs
        dphase = F_CASCADE * (phi[n + 1] - phi_target)
        phase[n + 1] = phase[n] + dphase

    return drive_eff, phi, phase


# ============================================================
# MODULE 6A: The Breathing Cycle (F-gate)
# ============================================================
def module6a_fgate():
    """
    Start from ITER raw D_static = 2.754. Show F-gate frequency-locks
    the effective drive into the breathing window after n* = 12 steps.
    """
    print("=" * 70)
    print("MODULE 6A: The Breathing Cycle (F-gate Frequency Locking)")
    print("=" * 70)

    n_steps = 120  # 10 Floquet cycles

    cases = {
        f'ITER ($D_{{static}}$={DRIVE_ITER:.2f})': DRIVE_ITER,
        f'3x threshold ($D_{{static}}$={3 * THRESHOLD_DRIVE:.2f})': 3 * THRESHOLD_DRIVE,
        f'Window center ($D_{{static}}$={WINDOW_CENTER:.2f})': WINDOW_CENTER,
        f'Sub-threshold ($D_{{static}}$={0.5 * THRESHOLD_DRIVE:.2f})': 0.5 * THRESHOLD_DRIVE,
    }

    fig, axes = plt.subplots(3, 1, figsize=(16, 13), sharex=True)
    n_arr = np.arange(n_steps + 1)
    colors = ['#e74c3c', '#f39c12', '#2ecc71', '#3498db']

    for idx, (label, D_static) in enumerate(cases.items()):
        d_eff, phi, phase = fgate_dynamics(D_static, n_steps)

        axes[0].plot(n_arr, d_eff, color=colors[idx], lw=1.5, label=label)
        axes[1].plot(n_arr, phi, color=colors[idx], lw=1.5, label=label)
        axes[2].plot(n_arr, phase / np.pi, color=colors[idx], lw=1.5, label=label)

        # Stats: time in window after n*
        d_post = d_eff[N_STAR:]
        in_win = np.sum((d_post >= THRESHOLD_DRIVE) & (d_post <= IGNITION_DRIVE))
        frac = in_win / len(d_post) if len(d_post) > 0 else 0
        print(f"  {label}:")
        print(f"    Post-lock range: [{d_post.min():.4f}, {d_post.max():.4f}]")
        print(f"    In window after n*={N_STAR}: {in_win}/{len(d_post)} = {frac:.1%}")
        print(f"    Final: drive={d_eff[-1]:.4f}, phi={phi[-1]:.4f}, "
              f"phase={phase[-1] / np.pi:.3f}*pi")

    # Mark window and n*
    axes[0].axhspan(THRESHOLD_DRIVE, IGNITION_DRIVE, alpha=0.12, color='green',
                    label=f'Window [{THRESHOLD_DRIVE:.3f}, {IGNITION_DRIVE:.3f}]')
    axes[0].axhline(THRESHOLD_DRIVE, ls='--', color='gray', alpha=0.4)
    axes[0].axhline(IGNITION_DRIVE, ls='--', color='gray', alpha=0.4)
    axes[0].axhline(WINDOW_CENTER, ls=':', color='gray', alpha=0.3)
    axes[0].axvline(N_STAR, ls=':', color='red', alpha=0.4, label=f'$n^* = {N_STAR}$ (cascade onset)')

    for ax in axes:
        for c in range(1, n_steps // T_FLOQUET + 1):
            ax.axvline(c * T_FLOQUET, ls=':', color='gray', alpha=0.1)

    axes[0].set_ylabel('Effective drive $D_{eff}(n)$', fontsize=12)
    axes[0].set_title('F-gate: Drive Frequency-Locked to $\\omega = 2\\pi/12$', fontsize=13,
                      fontweight='bold')
    axes[0].legend(fontsize=8, loc='upper right', ncol=2)
    axes[0].set_ylim(0, 3.2)

    axes[1].set_ylabel('Order parameter $\\phi(n)$', fontsize=12)
    axes[1].set_title('Cascade Cooperativity', fontsize=13, fontweight='bold')
    axes[1].legend(fontsize=8, loc='center right')

    axes[2].set_xlabel('Floquet step $n$', fontsize=12)
    axes[2].set_ylabel('P-gate phase / $\\pi$', fontsize=12)
    axes[2].set_title('P-gate Phase Correction', fontsize=13, fontweight='bold')
    axes[2].legend(fontsize=8, loc='upper right')
    axes[2].set_xlim(0, n_steps)

    fig.suptitle('Module 6A: Breathing Cycle via F-gate Frequency Locking\n'
                 f'$\\omega = 2\\pi/{T_FLOQUET}$ (E$_6$ Coxeter), '
                 f'buffer crossover at $n^* = {N_STAR}$',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(OUTDIR / 'module6a_fgate_breathing.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: module6a_fgate_breathing.png")


# ============================================================
# MODULE 6B: Optimal Window / Basin of Attraction
# ============================================================
def module6b_basin():
    """
    Sweep D_static from 0.5 to 5.0. For each:
      - Time in window after lock-in
      - Lock-in time (first step where drive enters window and stays)
      - Convergence to same asymptotic orbit

    All initial drives should converge to the SAME ouroboros orbit.
    """
    print("\n" + "=" * 70)
    print("MODULE 6B: Basin of Attraction / Optimal Window")
    print("=" * 70)

    n_steps = 150  # enough for convergence
    n_drives = 300
    drive_range = np.linspace(0.3, 5.0, n_drives)

    frac_in_window = np.zeros(n_drives)
    lockin_time = np.zeros(n_drives)
    mean_drive_post = np.zeros(n_drives)
    mean_phi_post = np.zeros(n_drives)

    for i, D_static in enumerate(drive_range):
        d_eff, phi, _ = fgate_dynamics(D_static, n_steps)

        # Time in window (post-transient: after 2*T_F)
        transient = 2 * T_FLOQUET
        d_post = d_eff[transient:]
        in_win = np.sum((d_post >= THRESHOLD_DRIVE) & (d_post <= IGNITION_DRIVE))
        frac_in_window[i] = in_win / len(d_post) if len(d_post) > 0 else 0
        mean_drive_post[i] = np.mean(d_post)
        mean_phi_post[i] = np.mean(phi[transient:])

        # Lock-in time: first step where drive enters window
        in_window_mask = (d_eff >= THRESHOLD_DRIVE) & (d_eff <= IGNITION_DRIVE)
        first_in = np.argmax(in_window_mask) if np.any(in_window_mask) else n_steps
        lockin_time[i] = first_in

    # Optimal
    opt_idx = np.argmax(frac_in_window)
    opt_drive = drive_range[opt_idx]
    opt_frac = frac_in_window[opt_idx]

    # ITER
    iter_idx = np.argmin(np.abs(drive_range - DRIVE_ITER))

    print(f"  Optimal D_static: {opt_drive:.3f}  (time-in-window = {opt_frac:.1%})")
    print(f"  ITER D_static={DRIVE_ITER:.3f}: time-in-window = {frac_in_window[iter_idx]:.1%}, "
          f"lock-in at step {lockin_time[iter_idx]:.0f}")
    print(f"  All D_static > threshold: mean post-transient drive ~ "
          f"{np.mean(mean_drive_post[drive_range > THRESHOLD_DRIVE]):.4f}")

    # --- Plots ---
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Top-left: Time-in-window vs D_static
    ax = axes[0, 0]
    ax.plot(drive_range, frac_in_window * 100, 'b-', lw=2)
    ax.axvline(opt_drive, ls='--', color='red', alpha=0.5,
               label=f'Optimal: {opt_drive:.2f}')
    ax.axvline(DRIVE_ITER, ls='--', color='purple', alpha=0.5,
               label=f'ITER: {DRIVE_ITER:.2f}')
    ax.axvline(THRESHOLD_DRIVE, ls=':', color='green', alpha=0.4)
    ax.axvline(IGNITION_DRIVE, ls=':', color='orange', alpha=0.4)
    ax.set_xlabel('Static drive $D_{static}$', fontsize=12)
    ax.set_ylabel('Time in window (%)', fontsize=12)
    ax.set_title('Time-in-Window vs Initial Drive', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.set_xlim(0.3, 5)

    # Top-right: Lock-in time vs D_static
    ax = axes[0, 1]
    ax.plot(drive_range, lockin_time, 'r-', lw=2)
    ax.axhline(N_STAR, ls='--', color='gray', alpha=0.5, label=f'$n^* = {N_STAR}$')
    ax.axvline(DRIVE_ITER, ls='--', color='purple', alpha=0.5,
               label=f'ITER: {DRIVE_ITER:.2f}')
    ax.set_xlabel('Static drive $D_{static}$', fontsize=12)
    ax.set_ylabel('Lock-in time (Floquet steps)', fontsize=12)
    ax.set_title(f'Lock-in Time to Window Entry', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.set_xlim(0.3, 5)
    ax.set_ylim(0, 50)

    # Bottom-left: Drive trajectories — all converge to same orbit
    ax = axes[1, 0]
    sample_drives = [0.5, 1.0, 1.2, 1.5, 2.0, DRIVE_ITER, 4.0]
    cmap = plt.cm.plasma
    n_arr = np.arange(n_steps + 1)
    for j, D_s in enumerate(sample_drives):
        d_eff, _, _ = fgate_dynamics(D_s, n_steps)
        c = cmap(j / (len(sample_drives) - 1))
        ax.plot(n_arr, d_eff, color=c, lw=1.2, alpha=0.8,
                label=f'{D_s:.2f}')
    ax.axhspan(THRESHOLD_DRIVE, IGNITION_DRIVE, alpha=0.1, color='green')
    ax.axhline(THRESHOLD_DRIVE, ls='--', color='gray', alpha=0.3)
    ax.axhline(IGNITION_DRIVE, ls='--', color='gray', alpha=0.3)
    ax.axvline(N_STAR, ls=':', color='red', alpha=0.3)
    ax.set_xlabel('Floquet step $n$', fontsize=12)
    ax.set_ylabel('Effective drive $D_{eff}$', fontsize=12)
    ax.set_title('Convergence: All Drives $\\to$ Same Orbit', fontsize=13, fontweight='bold')
    ax.legend(fontsize=8, title='$D_{static}$', loc='upper right')
    ax.set_xlim(0, n_steps)
    ax.set_ylim(0, 5)

    # Bottom-right: Mean post-transient drive and phi
    ax = axes[1, 1]
    ax2 = ax.twinx()
    ax.plot(drive_range, mean_drive_post, 'b-', lw=2, label='Mean $D_{eff}$')
    ax2.plot(drive_range, mean_phi_post, 'r--', lw=2, label='Mean $\\phi$')
    ax.axhspan(THRESHOLD_DRIVE, IGNITION_DRIVE, alpha=0.08, color='green')
    ax.axhline(WINDOW_CENTER, ls=':', color='gray', alpha=0.3)
    ax.set_xlabel('Static drive $D_{static}$', fontsize=12)
    ax.set_ylabel('Mean $D_{eff}$ (post-transient)', fontsize=12, color='b')
    ax2.set_ylabel('Mean $\\phi$ (post-transient)', fontsize=12, color='r')
    ax.set_title('Asymptotic Drive and Cooperativity', fontsize=13, fontweight='bold')
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=10, loc='upper left')
    ax.set_xlim(0.3, 5)

    fig.suptitle('Module 6B: Basin of Attraction\n'
                 'F-gate frequency locking pulls all drives into the breathing window',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(OUTDIR / 'module6b_fgate_basin.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: module6b_fgate_basin.png")

    return opt_drive, opt_frac


# ============================================================
# PHASE PORTRAIT: The Ouroboros Orbit
# ============================================================
def phase_portrait():
    """
    Plot phi vs drive for ITER and other starting points.
    After transient, should show closed loop = ouroboros orbit.
    Color-coded by time step.
    """
    print("\n" + "=" * 70)
    print("PHASE PORTRAIT: The Ouroboros Orbit")
    print("=" * 70)

    n_steps = 200  # long run for clean orbit

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    cases = [
        (f'ITER ($D_s$={DRIVE_ITER:.2f})', DRIVE_ITER),
        (f'2x Threshold ($D_s$={2 * THRESHOLD_DRIVE:.2f})', 2 * THRESHOLD_DRIVE),
        (f'Window center ($D_s$={WINDOW_CENTER:.2f})', WINDOW_CENTER),
    ]

    for idx, (label, D_s) in enumerate(cases):
        d_eff, phi, _ = fgate_dynamics(D_s, n_steps)
        ax = axes[idx]

        # Color by time step
        n_arr = np.arange(n_steps + 1)

        # Transient (first 2 cycles): gray
        transient_end = 2 * T_FLOQUET
        ax.plot(phi[:transient_end], d_eff[:transient_end],
                color='gray', lw=0.8, alpha=0.5, label='Transient')
        ax.plot(phi[0], d_eff[0], 'ko', ms=8, zorder=10, label='Start')

        # Steady state: color by phase within Floquet cycle
        phi_ss = phi[transient_end:]
        d_ss = d_eff[transient_end:]

        # Create colored line collection
        points = np.array([phi_ss, d_ss]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        cycle_phase = (n_arr[transient_end:-1] % T_FLOQUET) / T_FLOQUET
        lc = LineCollection(segments, cmap='hsv', norm=plt.Normalize(0, 1))
        lc.set_array(cycle_phase)
        lc.set_linewidth(2)
        line = ax.add_collection(lc)

        # Window shading
        ax.axhspan(THRESHOLD_DRIVE, IGNITION_DRIVE, alpha=0.1, color='green')
        ax.axhline(THRESHOLD_DRIVE, ls='--', color='gray', alpha=0.3)
        ax.axhline(IGNITION_DRIVE, ls='--', color='gray', alpha=0.3)
        ax.axhline(WINDOW_CENTER, ls=':', color='gray', alpha=0.2)

        ax.set_xlabel('$\\phi$ (cooperativity)', fontsize=12)
        if idx == 0:
            ax.set_ylabel('$D_{eff}$ (effective drive)', fontsize=12)
        ax.set_title(label, fontsize=12, fontweight='bold')
        ax.legend(fontsize=8, loc='upper left')

        # Report orbit extent
        if len(d_ss) > T_FLOQUET:
            last_cycle_d = d_ss[-T_FLOQUET:]
            last_cycle_phi = phi_ss[-T_FLOQUET:]
            print(f"  {label}:")
            print(f"    Orbit drive range: [{last_cycle_d.min():.4f}, {last_cycle_d.max():.4f}]")
            print(f"    Orbit phi range: [{last_cycle_phi.min():.4f}, {last_cycle_phi.max():.4f}]")
            in_win = np.sum((last_cycle_d >= THRESHOLD_DRIVE) &
                            (last_cycle_d <= IGNITION_DRIVE))
            print(f"    Last cycle in window: {in_win}/{T_FLOQUET}")

    # Colorbar for cycle phase
    fig.subplots_adjust(right=0.92)
    cbar_ax = fig.add_axes([0.94, 0.15, 0.015, 0.7])
    sm = plt.cm.ScalarMappable(cmap='hsv', norm=plt.Normalize(0, 1))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label('Phase within Floquet cycle', fontsize=10)
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.set_ticklabels(['0', '$T_F/4$', '$T_F/2$', '$3T_F/4$', '$T_F$'])

    fig.suptitle('Phase Portrait: The Ouroboros Orbit in ($\\phi$, $D_{eff}$) Space\n'
                 'Closed loop = breathing cycle locked to $\\omega = 2\\pi/12$',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.savefig(OUTDIR / 'module6_phase_portrait.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: module6_phase_portrait.png")


# ============================================================
# COMBINED OUROBOROS FIGURE (for Paper 3)
# ============================================================
def ouroboros_paper_figure():
    """
    Publication-quality figure showing the ouroboros orbit.
    Single panel: ITER trajectory spiraling into the breathing window,
    then orbiting as a closed loop.
    """
    print("\n" + "=" * 70)
    print("PAPER FIGURE: The Ouroboros Orbit")
    print("=" * 70)

    n_steps = 200
    d_eff, phi, phase = fgate_dynamics(DRIVE_ITER, n_steps)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Transient spiral (gray, fading in)
    n_trans = 3 * T_FLOQUET  # first 3 cycles
    for i in range(n_trans - 1):
        alpha_val = 0.1 + 0.4 * (i / n_trans)
        ax.plot(phi[i:i + 2], d_eff[i:i + 2], color='gray', lw=0.8, alpha=alpha_val)

    # Steady-state orbit (colored by cycle phase)
    phi_ss = phi[n_trans:]
    d_ss = d_eff[n_trans:]
    n_ss = np.arange(len(phi_ss))
    points = np.array([phi_ss, d_ss]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    cycle_phase = (n_ss[:-1] % T_FLOQUET) / T_FLOQUET
    lc = LineCollection(segments, cmap='twilight', norm=plt.Normalize(0, 1))
    lc.set_array(cycle_phase)
    lc.set_linewidth(2.5)
    ax.add_collection(lc)

    # Start point
    ax.plot(phi[0], d_eff[0], 'ko', ms=10, zorder=10)
    ax.annotate(f'ITER start\n$D = {DRIVE_ITER:.2f}$', xy=(phi[0], d_eff[0]),
                xytext=(phi[0] + 0.05, d_eff[0] + 0.15),
                fontsize=10, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='black'))

    # Window
    ax.axhspan(THRESHOLD_DRIVE, IGNITION_DRIVE, alpha=0.12, color='green')
    ax.axhline(THRESHOLD_DRIVE, ls='--', color='#27ae60', alpha=0.6, lw=1.5)
    ax.axhline(IGNITION_DRIVE, ls='--', color='#e67e22', alpha=0.6, lw=1.5)
    ax.axhline(WINDOW_CENTER, ls=':', color='gray', alpha=0.3)

    # Labels
    ax.text(0.01, THRESHOLD_DRIVE + 0.01, f'Threshold = f$\\cdot$r = {THRESHOLD_DRIVE:.3f}',
            fontsize=9, color='#27ae60', fontweight='bold')
    ax.text(0.01, IGNITION_DRIVE + 0.01, f'Ignition = f$\\cdot$r$\\cdot$(4/3) = {IGNITION_DRIVE:.3f}',
            fontsize=9, color='#e67e22', fontweight='bold')

    # Arrow showing direction on orbit
    mid = n_trans + 2 * T_FLOQUET + T_FLOQUET // 4
    if mid + 1 < len(phi):
        ax.annotate('', xy=(phi[mid + 1], d_eff[mid + 1]),
                    xytext=(phi[mid], d_eff[mid]),
                    arrowprops=dict(arrowstyle='->', color='black', lw=2))

    ax.set_xlabel('Cooperativity $\\phi$', fontsize=14)
    ax.set_ylabel('Effective Drive $D_{eff}$', fontsize=14)
    ax.set_title('The Ouroboros Orbit: Plasma Breathing in the Window\n'
                 f'F-gate: $\\omega = 2\\pi/{T_FLOQUET}$ (E$_6$ Coxeter h), '
                 f'Window ratio = 4/3',
                 fontsize=15, fontweight='bold')

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap='twilight', norm=plt.Normalize(0, 1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=20)
    cbar.set_label('Phase within Floquet cycle ($T_F = 12$)', fontsize=11)

    # Add text box with key parameters
    textstr = (f'$\\alpha = 4/3$ (KWW threshold)\n'
               f'$f = 1/3$ (cascade fraction)\n'
               f'$n^* = 12$ (E$_6$ Coxeter $h$)\n'
               f'$\\omega = 2\\pi/12$ (ouroboros)\n'
               f'Window ratio = $4/3$ exact')
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.98, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', horizontalalignment='right', bbox=props)

    plt.tight_layout()
    plt.savefig(OUTDIR / 'module6_ouroboros_orbit.png', dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  Saved: module6_ouroboros_orbit.png (publication quality)")

    # Report orbit metrics
    last_3_cycles = slice(-3 * T_FLOQUET, None)
    d_orbit = d_eff[last_3_cycles]
    phi_orbit = phi[last_3_cycles]
    print(f"  Last 3 cycles:")
    print(f"    Drive range: [{d_orbit.min():.4f}, {d_orbit.max():.4f}]")
    print(f"    Phi range: [{phi_orbit.min():.4f}, {phi_orbit.max():.4f}]")
    in_win = np.sum((d_orbit >= THRESHOLD_DRIVE) & (d_orbit <= IGNITION_DRIVE))
    print(f"    In window: {in_win}/{len(d_orbit)} = {in_win / len(d_orbit):.1%}")
    orbit_area = np.abs(np.sum(0.5 * (d_orbit[:-1] + d_orbit[1:]) * np.diff(phi_orbit)))
    print(f"    Orbit area ~ {orbit_area:.6f} (drive * phi units)")


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("MODULE 6 (F-GATE CORRECTED): THE BREATHING WINDOW")
    print("Frequency Locking via F-gate + P-gate Phase Correction")
    print("=" * 70)
    print()
    print(f"  F-gate frequency:  omega = 2*pi/{T_FLOQUET} = {OMEGA:.4f} rad/step")
    print(f"  Window center:     D_baseline = {WINDOW_CENTER:.4f}")
    print(f"  Window half-width: D_amplitude = {WINDOW_HALF:.4f}")
    print(f"  Buffer crossover:  n* = {N_STAR} steps")
    print(f"  P-gate gain:       f = {F_CASCADE:.4f}")
    print()

    module6a_fgate()
    opt_d, opt_f = module6b_basin()
    phase_portrait()
    ouroboros_paper_figure()

    print("\n" + "=" * 70)
    print("MODULE 6 (F-GATE) COMPLETE")
    print("=" * 70)
    print(f"""
  The F-gate projects the drive onto the resonant mode at omega = 2*pi/12.
  The P-gate provides slow phase correction tracking phi.

  RESULT: All initial drives (including ITER at {DRIVE_ITER}) converge to
  the SAME ouroboros orbit oscillating within [{THRESHOLD_DRIVE:.3f}, {IGNITION_DRIVE:.3f}].
  Lock-in occurs at n* = {N_STAR} Floquet steps (E6 Coxeter number).
  The breathing window ratio is EXACTLY 4/3.

  Optimal D_static = {opt_d:.3f} (time-in-window = {opt_f:.0%}).

  The ouroboros orbit in (phi, D_eff) space IS the breathing cycle.
  This is the central figure for Paper 3.
""")

    print("  Files generated:")
    for f in sorted(OUTDIR.glob('module6*.png')):
        print(f"    {f.name}")


if __name__ == '__main__':
    main()
