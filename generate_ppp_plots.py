import os
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors

DEBUG = False

def dbg(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

# ------------------------------------------------------------
# Pfade
# ------------------------------------------------------------
MSC_PATH = "/storage/research/aiub_u_camp/CK_ZDGNSS/MSC"
OUTPUT_DIR = "/storage/homefs/ck18y530/monitoring-plots/plots/ppp"
TMP_DIR = "/storage/homefs/ck18y530/monitoring-plots/tmp"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

# ------------------------------------------------------------
# Letzte N MSC-Ordner
# ------------------------------------------------------------
def get_last_n_folders(n=60):
    folders = [f for f in os.listdir(MSC_PATH) if f.startswith("MSC_")]
    folders.sort()
    return folders[-n:]

# ------------------------------------------------------------
# Folder → yy/ddd
# ------------------------------------------------------------
def folder_to_date(folder_name):
    yyddd = folder_name.split("_")[1]
    return f"{yyddd[:2]}/{yyddd[2:]}"

# ------------------------------------------------------------
# XTRRMS Parser
# ------------------------------------------------------------
def parse_xtrrms(file_path):
    rms_val = np.nan
    with open(file_path, "r") as f:
        for line in f:
            if "Rms:" in line:
                m = re.search(r"Rms:\s*([0-9.+-Ee]+)", line)
                if m:
                    rms_val = float(m.group(1))
                    break
    return rms_val

# ------------------------------------------------------------
# XTRREP Parser
# ------------------------------------------------------------
def parse_xtrrep(file_path):
    epochs = []
    reading = False
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("--------------------------------------------------------------------------------"):
                reading = not reading
                continue
            if reading:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        epoch = float(parts[0])
                        n, e, u = map(float, parts[1:4])
                        epochs.append([epoch, n, e, u])
                    except ValueError:
                        continue
    return np.array(epochs) if epochs else np.empty((0, 4))

# ------------------------------------------------------------
# NaN-Markierung
# ------------------------------------------------------------
def mark_nan_days(ax, x, y):
    ymin, ymax = ax.get_ylim()
    nan_idx = np.isnan(y)
    if np.any(nan_idx):
        ax.scatter(
            np.array(x)[nan_idx],
            np.full(np.sum(nan_idx), ymin),
            marker="x",
            color="gray",
            zorder=5
        )
        ax.set_ylim(ymin, ymax)

# ------------------------------------------------------------
# Funktion: N/E/U nach Tag färben
# ------------------------------------------------------------
def plot_by_day(ax, epochs, values):
    """
    epochs : 1D array (epoch)
    values : 1D array (N/E/U in mm)
    """
    days = np.floor(epochs).astype(int)
    unique_days = np.unique(days)

    cmap = cm.get_cmap("viridis", len(unique_days))
    for i, d in enumerate(unique_days):
        idx = days == d
        ax.plot(
            epochs[idx],
            values[idx],
            marker="o",
            linestyle="-",
            color=cmap(i),
            markersize=3
        )

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    stations = ["WGTN", "CPVG", "SCOR", "ROTH", "ZIM3"]
    last_folders = get_last_n_folders()

    # --------------------------------------------------------
    # Datenaufbereitung
    # --------------------------------------------------------
    for station in stations:
        rms_file_path = os.path.join(TMP_DIR, f"{station}_RMS.txt")
        rep_file_path = os.path.join(TMP_DIR, f"{station}_REP.txt")

        # TMP-Files vor Neuaufbau löschen
        if os.path.exists(rms_file_path):
            os.remove(rms_file_path)

        if os.path.exists(rep_file_path):
            os.remove(rep_file_path)

        all_rms = []
        all_rms_dates = []
        all_epochs = []

        for folder in last_folders:
            yyddd = folder.split("_")[1]
            day_label = folder_to_date(folder)

            # RMS
            xtrrms_fname = f"XTRRMS{station}{yyddd}0.SUM"
            xtrrms_path = os.path.join(MSC_PATH, folder, xtrrms_fname)
            rms_val = parse_xtrrms(xtrrms_path) if os.path.exists(xtrrms_path) else np.nan
            all_rms.append(rms_val)
            all_rms_dates.append(day_label)

            # REP
            xtrrep_fname = f"XTRREP{station}{yyddd}0.SUM"
            xtrrep_path = os.path.join(MSC_PATH, folder, xtrrep_fname)
            epochs = parse_xtrrep(xtrrep_path) if os.path.exists(xtrrep_path) else np.empty((0, 4))
            if epochs.size > 0:
                all_epochs.append(epochs)

        # RMS speichern
        rms_array = np.column_stack([all_rms_dates, all_rms])
        np.savetxt(rms_file_path, rms_array, fmt="%s", delimiter=",")

        # REP speichern
        if all_epochs:
            full_epochs = np.vstack(all_epochs)
            np.savetxt(rep_file_path, full_epochs, fmt="%.6f")

    # --------------------------------------------------------
    # PLOTS
    # --------------------------------------------------------
    for station in stations:
        rms_file_path = os.path.join(TMP_DIR, f"{station}_RMS.txt")
        rms_data = np.loadtxt(rms_file_path, delimiter=",", dtype=str)
        rms_dates = rms_data[:, 0]
        rms_vals = rms_data[:, 1].astype(float)

        fig, axs = plt.subplots(4, 1, figsize=(14, 12), sharex=False)
        fig.suptitle(f"Station {station}", fontsize=20, fontweight="bold")

        # RMS
        axs[0].plot(rms_dates, rms_vals, marker="o")
        mark_nan_days(axs[0], np.arange(len(rms_vals)), rms_vals)
        axs[0].set_ylabel("[mm]", fontsize=14)
        axs[0].set_title("RMS", fontsize=16)
        axs[0].tick_params(axis="x", rotation=45, labelsize=12)
        axs[0].tick_params(axis="y", labelsize=12)

        # REP laden
        rep_file_path = os.path.join(TMP_DIR, f"{station}_REP.txt")
        if os.path.exists(rep_file_path):
            epochs = np.loadtxt(rep_file_path)
            if epochs.ndim == 1:
                epochs = np.empty((0, 4))
        else:
            epochs = np.empty((0, 4))

        if epochs.size > 0:
            epochs_mm = epochs.copy()
            epochs_mm[:, 1:4] *= 1000.0  # m → mm

            std_n = np.nanstd(epochs_mm[:, 1])
            std_e = np.nanstd(epochs_mm[:, 2])
            std_u = np.nanstd(epochs_mm[:, 3])
        else:
            epochs_mm = np.empty((0, 4))
            std_n = std_e = std_u = np.nan

        # North
        if epochs_mm.size > 0:
            plot_by_day(axs[1], epochs_mm[:, 0], epochs_mm[:, 1])
        axs[1].set_ylabel("[mm]", fontsize=14)
        axs[1].set_title("North", fontsize=16)
        axs[1].text(
            0.02, 0.95, f"σ = {std_n:.3f} mm",
            transform=axs[1].transAxes,
            fontsize=12, va="top"
        )

        # East
        if epochs_mm.size > 0:
            plot_by_day(axs[2], epochs_mm[:, 0], epochs_mm[:, 2])
        axs[2].set_ylabel("[mm]", fontsize=14)
        axs[2].set_title("East", fontsize=16)
        axs[2].text(
            0.02, 0.95, f"σ = {std_e:.3f} mm",
            transform=axs[2].transAxes,
            fontsize=12, va="top"
        )

        # Up
        if epochs_mm.size > 0:
            plot_by_day(axs[3], epochs_mm[:, 0], epochs_mm[:, 3])
        axs[3].set_ylabel("[mm]", fontsize=14)
        axs[3].set_title("Up", fontsize=16)
        axs[3].set_xlabel("Epoch", fontsize=14)
        axs[3].text(
            0.02, 0.95, f"σ = {std_u:.3f} mm",
            transform=axs[3].transAxes,
            fontsize=12, va="top"
        )

        for ax in axs:
            ax.tick_params(axis="both", labelsize=12)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(os.path.join(OUTPUT_DIR, f"{station}_plot.png"))
        plt.close()
