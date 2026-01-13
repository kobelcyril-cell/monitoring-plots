#!/usr/bin/env python3
import os
import re
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

DEBUG = False
MSC_PATH = "/storage/research/aiub_u_camp/CK_ZDGNSS/MSC"
OUTPUT_DIR = "/storage/homefs/ck18y530/monitoring-plots/plots/comparisons"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def dbg(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

# ----------------------------
# Letzte N MSC-Ordner
# ----------------------------
def get_last_n_folders(n=40):
    folders = [f for f in os.listdir(MSC_PATH) if f.startswith("MSC_")]
    folders.sort()
    return folders[-n:]

def folder_to_date(folder_name):
    yyddd = folder_name.split("_")[1]
    return datetime(2000 + int(yyddd[:2]), 1, 1) + timedelta(days=int(yyddd[2:])-1)

# ----------------------------
# Parsing SUMMARY-Dateien
# ----------------------------
def parse_summary_file(file_path):
    dbg(f"Parse {file_path}")
    data = {}
    keys = [
        "mean_dX","mean_dY","mean_dUT1",
        "mean_Pos_R","mean_Pos_A","mean_Pos_C",
        "RMS_Pos_R","RMS_Pos_A","RMS_Pos_C",
        "CLK_ALL","CLK_GLONASS","CLK_GPS",
        "CLK_ALL_RMS","CLK_GLONASS_RMS","CLK_GPS_RMS",
        "CLK_ALL_STD","CLK_GLONASS_STD","CLK_GPS_STD",
        "PRE_ALL","PRE_GPS","PRE_GLO","PRE_GAL",
        "CRD_Total_N","CRD_Total_E","CRD_Total_U",
        "H_F1I_TX","H_F1I_TY","H_F1I_TZ","H_F1I_RX","H_F1I_RY","H_F1I_RZ","H_F1I_SCALE","H_F1I_RMS",
        "H_F1I_TX_STD","H_F1I_TY_STD","H_F1I_TZ_STD","H_F1I_RX_STD","H_F1I_RY_STD","H_F1I_RZ_STD","H_F1I_SCALE_STD",
        "H_F1_TX","H_F1_TY","H_F1_TZ","H_F1_RX","H_F1_RY","H_F1_RZ","H_F1_SCALE","H_F1_RMS",
        "H_F1_TX_STD","H_F1_TY_STD","H_F1_TZ_STD","H_F1_RX_STD","H_F1_RY_STD","H_F1_RZ_STD","H_F1_SCALE_STD"
    ]
    for k in keys:
        data[k] = np.nan

    try:
        with open(file_path,'r') as f:
            lines = f.read().splitlines()

        # ERP Comparison
        idx = next((i for i,l in enumerate(lines) if "ERP Rate Differences:" in l), None)
        if idx is not None:
            vals = np.fromstring(lines[idx+2], sep=' ')
            data["mean_dX"] = vals[0]*1e6
            data["mean_dY"] = vals[1]*1e6
            data["mean_dUT1"] = vals[2]*1e6

        # STD Comparison
        idx = next((i for i,l in enumerate(lines) if "STD Comparison:" in l), None)
        if idx is not None:
            vals = np.fromstring(lines[idx+2], sep=' ')*1e3
            data["mean_Pos_R"], data["mean_Pos_A"], data["mean_Pos_C"] = vals[0:3]
            data["RMS_Pos_R"], data["RMS_Pos_A"], data["RMS_Pos_C"] = vals[3:6]

#        # CLK Comparison
#        idx = next((i for i,l in enumerate(lines) if "CLK Comparison:" in l), None)
#        if idx is not None:
#            vals_ALL = np.fromstring(' '.join(lines[idx+2].split()[1:]), sep=' ')
#            vals_GLONASS = np.fromstring(' '.join(lines[idx+3].split()[1:]), sep=' ')
#            vals_GPS = np.fromstring(' '.join(lines[idx+4].split()[1:]), sep=' ')
#            data.update({
#                "CLK_ALL": vals_ALL[0]*1e9, "CLK_ALL_RMS": vals_ALL[1]*1e9, "CLK_ALL_STD": vals_ALL[2]*1e9,
#                "CLK_GLONASS": vals_GLONASS[0]*1e9, "CLK_GLONASS_RMS": vals_GLONASS[1]*1e9, "CLK_GLONASS_STD": vals_GLONASS[2]*1e9,
#                "CLK_GPS": vals_GPS[0]*1e9, "CLK_GPS_RMS": vals_GPS[1]*1e9, "CLK_GPS_STD": vals_GPS[2]*1e9
#            })

        # PRE Comparison
        idx = next((i for i,l in enumerate(lines) if "PRE Comparison:" in l), None)
        if idx is not None:
            PRE_ALL = np.fromstring(' '.join(lines[idx+2].split()[1:]), sep=' ')
            PRE_GPS = np.fromstring(' '.join(lines[idx+3].split()[1:]), sep=' ')
            PRE_GLO = np.fromstring(' '.join(lines[idx+4].split()[1:]), sep=' ')
            PRE_GAL = np.fromstring(' '.join(lines[idx+5].split()[1:]), sep=' ')
            data.update({
                "PRE_ALL": PRE_ALL[0]*1e2, "PRE_GPS": PRE_GPS[0]*1e2, "PRE_GLO": PRE_GLO[0]*1e2, "PRE_GAL": PRE_GAL[0]*1e2
            })

        # CRD Comparison
        idx = next((i for i,l in enumerate(lines) if "CRD Comparison:" in l), None)
        if idx is not None:
            vals = np.fromstring(lines[idx+2], sep=' ')
            data["CRD_Total_N"], data["CRD_Total_E"], data["CRD_Total_U"] = vals[0:3]

        def parse_helmert(idx_base, prefix):
            # Translation X, Y, Z
            for i, axis in enumerate(["X","Y","Z"]):
                line = lines[idx_base + 1 + i]
                m = re.search(r":\s*([-\d\.]+)\s*\+\-\s*([-\d\.]+)", line)
                if m:
                    data[f"{prefix}_T{axis}"] = float(m.group(1))      # Translation
                    data[f"{prefix}_T{axis}_STD"] = float(m.group(2))
                else:
                    data[f"{prefix}_T{axis}"] = np.nan
                    data[f"{prefix}_T{axis}_STD"] = np.nan
        
            # Rotation X, Y, Z (letzte Zahl vor '+-')
            for i, axis in enumerate(["X","Y","Z"]):
                line = lines[idx_base + 4 + i]  # ROTATION Zeilen stehen danach
                parts = line.strip().split()
                #print(parts[-4])
                # letzte Zahl vor '+-' = parts[-4], Standardabweichung = parts[-1] (ohne ")
                try:
                    val = float(parts[-4])
                    std = float(parts[-2].replace('"',''))
                    data[f"{prefix}_R{axis}"] = val
                    data[f"{prefix}_R{axis}_STD"] = std
                except:
                    data[f"{prefix}_R{axis}"] = np.nan
                    data[f"{prefix}_R{axis}_STD"] = np.nan

        
            # Scale Factor
            line = lines[idx_base + 7]
            m = re.search(r":\s*([-\d\.]+)\s*\+\-\s*([-\d\.]+)", line)
            if m:
                data[f"{prefix}_SCALE"] = float(m.group(1))
                data[f"{prefix}_SCALE_STD"] = float(m.group(2))
            else:
                data[f"{prefix}_SCALE"] = np.nan
                data[f"{prefix}_SCALE_STD"] = np.nan
        
            # RMS_OF_TRANSFORMATION
            line = lines[idx_base + 8]
            m = re.search(r"=\s*([-\d\.]+)", line)
            if m:
                data[f"{prefix}_RMS"] = float(m.group(1))
            else:
                data[f"{prefix}_RMS"] = np.nan



        idx = next((i for i,l in enumerate(lines) if "Helmert Parameters F1I_" in l), None)
        if idx is not None:
            parse_helmert(idx, "H_F1I")

        idx = next((i for i,l in enumerate(lines) if "Helmert Parameters F1," in l), None)
        if idx is not None:
            parse_helmert(idx, "H_F1")

        # Debug-Ausgabe
        #print(f"\n{os.path.basename(file_path)}:")
        for k in ["mean_dX","mean_dY","mean_dUT1","RMS_Pos_R","RMS_Pos_A","RMS_Pos_C",
                  "CLK_ALL","CLK_GLONASS","CLK_GPS","PRE_ALL","PRE_GPS","PRE_GLO","PRE_GAL",
                  "CRD_Total_N","CRD_Total_E","CRD_Total_U",
                  "H_F1I_TX","H_F1I_TY","H_F1I_TZ","H_F1I_RX","H_F1I_RY","H_F1I_RZ","H_F1I_SCALE","H_F1I_RMS",
                  "H_F1_TX","H_F1_TY","H_F1_TZ","H_F1_RX","H_F1_RY","H_F1_RZ","H_F1_SCALE","H_F1_RMS"]:
            val = data.get(k, np.nan)
            #print(f"  {k} = {val:.6f}")

    except Exception as e:
        dbg(f"Fehler beim Parsen {file_path}: {e}")

    return data

# ----------------------------
# NaN-sichere Extraktion
# ----------------------------
def safe_values(extractor, all_data, folders):
    vals = []
    for folder in folders:
        data = all_data.get(folder)
        if not data:
            vals.append(np.nan)
            continue
        try:
            v = extractor(data)
            vals.append(v if v is not None else np.nan)
        except:
            vals.append(np.nan)
    return np.array(vals, dtype=float)

# ----------------------------
# Plot helper (NaN als graues Kreuz)
# ----------------------------
def plot_with_nan_markers(ax, x, y, label=None, color=None, marker='o'):
    ax.plot(x, y, linestyle='-', marker=marker, color=color, label=label)
    for xi, yi in zip(x, y):
        if np.isnan(yi):
            ax.plot(xi, 0, 'x', color='gray')

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    last_folders = get_last_n_folders()
    x_labels = [folder_to_date(f) for f in last_folders]

    all_data = {}
    for folder in last_folders:
        file_id = folder.split("_")[1]
        fname = f"SUMMARY_1_F1I__F1I__F1IS_F1I__F1I__{file_id}.DAT"
        fpath = os.path.join(MSC_PATH, folder, fname)
        all_data[folder] = parse_summary_file(fpath) if os.path.exists(fpath) else None

    cmap = plt.get_cmap('tab10').colors

    # ----------------------------
    # ERP Plot
    # ----------------------------
    plt.figure(figsize=(10,5))
    for val,label,color in zip(["mean_dX","mean_dY","mean_dUT1"], ['ΔX-rate','ΔY-rate','ΔLOD'], cmap[:3]):
        y = safe_values(lambda d,k=val: d[k], all_data, last_folders)
        plot_with_nan_markers(plt.gca(), x_labels, y, label=label, color=color)
    plt.ylabel('ERP [μas / μs]')
    plt.title('Earth rotation parameter comparison to CODE')
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR,'erp_comparison.png'))
    plt.close()

    # ----------------------------
    # STD Comparison (Mean + RMS)
    # ----------------------------
    fig, axs = plt.subplots(2,1,figsize=(10,6), sharex=True)
    for val,label,color in zip(["mean_Pos_R","mean_Pos_A","mean_Pos_C"],['Radial','Along-track','Cross-track'], cmap[:3]):
        y = safe_values(lambda d,k=val: d[k], all_data, last_folders)
        plot_with_nan_markers(axs[0], x_labels, y, label=label, color=color)
    axs[0].set_ylabel('Mean [mm]')
    axs[0].set_title('Orbit Differences (STD-Orbit) to CODE')
    axs[0].grid(True)
    axs[0].legend(loc='upper left')

    for val,color in zip(["RMS_Pos_R","RMS_Pos_A","RMS_Pos_C"], cmap[:3]):
        y = safe_values(lambda d,k=val: d[k], all_data, last_folders)
        plot_with_nan_markers(axs[1], x_labels, y, color=color)
    axs[1].set_ylabel('RMS [mm]')
    axs[1].set_xlabel('Date')
    axs[1].grid(True)
    axs[1].legend(['Radial','Along-track','Cross-track'], loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR,'std_comparison.png'))
    plt.close()

    # # ----------------------------
    # # CLK Comparison
    # # ----------------------------
    # fig, axs = plt.subplots(2,1,figsize=(10,6), sharex=True)
    # for val,label,color in zip(["CLK_ALL","CLK_GLONASS","CLK_GPS"], ['All','GLONASS','GPS'], cmap[:3]):
    #     y = safe_values(lambda d,k=val: d[k], all_data, last_folders)
    #     plot_with_nan_markers(axs[0], x_labels, y, label=label, color=color)
    #     y_rms = safe_values(lambda d,k=val+"_RMS": d[k], all_data, last_folders)
    #     plot_with_nan_markers(axs[1], x_labels, y_rms, color=color)
    # axs[0].set_ylabel('Clock Bias [ns]')
    # axs[0].set_title('Clock Bias Comparison')
    # axs[0].grid(True)
    # axs[0].legend()
    # axs[1].set_ylabel('RMS [ns]')
    # axs[1].set_xlabel('Date')
    # axs[1].grid(True)
    # axs[1].legend(['All','GLONASS','GPS'])
    # plt.xticks(rotation=45)
    # plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR,'clk_comparison.png'))
    # plt.close()

    # ----------------------------
    # PRE Comparison
    # ----------------------------
    plt.figure(figsize=(10,5))
    for val,label,color in zip(["PRE_ALL","PRE_GPS","PRE_GLO","PRE_GAL"], ['All','GPS','GLONASS','Galileo'], cmap[:4]):
        y = safe_values(lambda d,k=val: d[k], all_data, last_folders)
        plot_with_nan_markers(plt.gca(), x_labels, y, label=label, color=color)
    plt.ylabel('3D RMS [cm]')
    plt.title('Precise orbit comparison to CODE')
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR,'pre_comparison.png'))
    plt.close()

    # ----------------------------
    # CRD Comparison
    # ----------------------------
    fig, axs = plt.subplots(3,1,figsize=(10,6), sharex=True)
    for val,label,color,ax in zip(["CRD_Total_N","CRD_Total_E","CRD_Total_U"],['N','E','U'], cmap[:3], axs):
        y = safe_values(lambda d,k=val: d[k], all_data, last_folders)
        plot_with_nan_markers(ax, x_labels, y, color=color)
        ax.set_ylabel(f'{label} [mm]')
        ax.grid(True)
    axs[-1].set_xlabel('Date')
    axs[0].set_title('Station coordinate comparison to CODE (RMS over all stations)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR,'crd_comparison.png'))
    plt.close()

    # ----------------------------
    # Helmert F1I / F1 Comparison
    # ----------------------------
    helmert_params = ['RMS','TX','TY','TZ','RX','RY','RZ','SCALE']
    F1I_vals = np.column_stack([safe_values(lambda d,k=k: d[f"H_F1I_{k}"], all_data, last_folders) for k in helmert_params])
    F1_vals  = np.column_stack([safe_values(lambda d,k=k: d[f"H_F1_{k}"], all_data, last_folders)  for k in helmert_params])

    fig, axs = plt.subplots(len(helmert_params),1, figsize=(10,14), sharex=True)
    for i,param in enumerate(helmert_params):
        plot_with_nan_markers(axs[i], x_labels, F1I_vals[:,i], label='Zero-difference', color=cmap[0], marker='o')
        plot_with_nan_markers(axs[i], x_labels, F1_vals[:,i], label='CODE', color=cmap[1], marker='s')
        axs[i].grid(True)
        if param == 'TX':
            axs[i].set_ylabel('TX [mm]')
        elif param == 'TY':
            axs[i].set_ylabel('TY [mm]')
        elif param == 'TZ':
            axs[i].set_ylabel('TZ [mm]')
        elif param == 'RX':
            axs[i].set_ylabel('RX [masec]')
        elif param == 'RY':
            axs[i].set_ylabel('RY [masec]')
        elif param == 'RZ':
            axs[i].set_ylabel('RZ [masec]')
        elif param=='SCALE':
            axs[i].set_ylabel('Scale [mm/km]')
        elif param=='RMS':
            axs[i].set_ylabel('RMS [mm]')
        if i==0:
            axs[i].legend(loc='upper right')
        if i != len(helmert_params)-1:
            axs[i].set_xticklabels([])
    axs[-1].set_xlabel('Date')
    axs[0].set_title('Helmert parameters (to IGB20)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR,'helmert_F1I_F1.png'))
    plt.close()
