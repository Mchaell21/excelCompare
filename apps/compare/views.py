import os
import openpyxl
import requests
import pandas as pd
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings 

def landing_page(request):
    """Halaman Utama untuk Memilih Mode Komparasi"""
    return render(request, 'home.html')

def compare_exceltoapi(request):
    results = []
    summary = {'total': 0, 'kurang': 0, 'lebih': 0, 'setara': 0}

    dasa_url = getattr(settings, 'DASA_URL', '').rstrip('/')
    secret_key = getattr(settings, 'X_SECRET_KEY_API_DBW', '')
    api_url = f"{dasa_url}"

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        try:
            excel_file.seek(0)
            df = None
            
            try:
                df = pd.read_excel(excel_file, header=None)
            except Exception:
                try:
                    excel_file.seek(0)
                    dfs = pd.read_html(excel_file)
                    if dfs:
                        df = dfs[0]
                except Exception as e_html:
                    raise Exception(f"Format file tidak valid atau rusak: {str(e_html)}")

            if df is None:
                raise Exception("Gagal membaca isi tabel dari file.")

            items_payload = []
            start_row = 20

            for idx in range(start_row, len(df)):
                val_b = df.iloc[idx, 0]   # Kolom A (Nama Item)
                val_l = df.iloc[idx, 11]  # Kolom L (Qty Excel)

                if pd.isna(val_b) or str(val_b).strip() == "":
                    break

                item_name = str(val_b).strip()
                try:
                    qty_excel = float(val_l) if not pd.isna(val_l) else 0.0
                    if qty_excel.is_integer():
                        qty_excel = int(qty_excel)
                except (ValueError, TypeError):
                    qty_excel = 0

                items_payload.append({
                    'item_name': item_name,
                    'qty_excel': qty_excel
                })

            if not items_payload:
                messages.warning(request, "Tidak ada data yang ditemukan mulai dari baris 20.")
                return render(request, 'exceltoapi.html')

            headers = {
                'X-Secret-Key-API-DBW': secret_key,
                'Content-Type': 'application/json'
            }
            try:
                response = requests.post(
                    api_url, 
                    json={'items': items_payload}, 
                    headers=headers,
                    timeout=15
                )

                if response.status_code == 200:
                    api_response_data = response.json()
                    api_response_map = {}
                    
                    items_list = []
                    if isinstance(api_response_data, list):
                        items_list = api_response_data
                    elif isinstance(api_response_data, dict):
                        items_list = api_response_data.get('data', [])

                    for item in items_list:
                        name = item.get('NameFromTaco') or item.get('item_name')
                        if name:
                            qoso = item.get('QOSO', 0) or 0
                            qa = item.get('QA', 0) or 0
                            qoh = item.get('QOH', 0) or 0
                            
                            api_response_map[name.strip()] = {
                                'qoso': qoso,
                                'qa': qa,
                                'qoh': qoh,
                                'total_api_qty': qoso + qa + qoh
                            }

                else:
                    messages.error(request, f"API Error [{response.status_code}]: {response.text}")
                    return render(request, 'exceltoapi.html', {'results': results, 'summary': summary})

                # Bandingkan data Excel dengan API
                for item in items_payload:
                    name = item['item_name']
                    excel_qty = item['qty_excel']

                    api_data = api_response_map.get(name, {'qoso': 0, 'qa': 0, 'qoh': 0, 'total_api_qty': 0})
                    
                    qoso = api_data['qoso']
                    qa = api_data['qa']
                    qoh = api_data['qoh']
                    api_qty = api_data['total_api_qty']
                    
                    diff = api_qty - excel_qty

                    if diff < 0:
                        status = 'kurang'    
                        summary['kurang'] += 1
                    elif diff > 0:
                        status = 'lebih'      
                        summary['lebih'] += 1
                    else:
                        status = 'setara' 
                        summary['setara'] += 1

                    results.append({
                        'item_name': name,
                        'excel_qty': excel_qty,
                        'qoso': qoso,
                        'qa': qa,
                        'qoh': qoh,
                        'api_qty': api_qty,
                        'diff': diff,
                        'status': status
                    })

                summary['total'] = len(results)

            except requests.RequestException as e:
                messages.error(request, f"Gagal menghubungi API: {str(e)}")

        except Exception as e:
            messages.error(request, f"Gagal memproses file: {str(e)}")

    return render(request, 'exceltoapi.html', {
        'results': results,
        'summary': summary
    })

def compare_exceltoexcel(request):
    results = []
    summary = {'total': 0, 'kurang': 0, 'lebih': 0, 'setara': 0}

    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')      # File Excel Opname (Fisik)
        system_file = request.FILES.get('system_file')    # File Excel Report Sistem (QuickBooks)

        if not excel_file or not system_file:
            messages.error(request, "Harap unggah kedua file Excel (File Opname dan File Sistem).")
            return render(request, 'exceltoexcel.html', {'results': results, 'summary': summary})

        try:
            excel_file.seek(0)
            df_opname = pd.read_excel(excel_file, header=None)
            
            opname_dict = {}
            start_row = 19  

            for idx in range(start_row, len(df_opname)):
                val_b = df_opname.iloc[idx, 0]   
                val_l = df_opname.iloc[idx, 11]  

                if pd.isna(val_b) or str(val_b).strip() == "":
                    continue

                item_name = str(val_b).strip()
                try:
                    qty_excel = float(val_l) if not pd.isna(val_l) else 0.0
                    if qty_excel.is_integer():
                        qty_excel = int(qty_excel)
                except (ValueError, TypeError):
                    qty_excel = 0

                opname_dict[item_name] = qty_excel

            if not opname_dict:
                messages.warning(request, "Tidak ada data item ditemukan pada File Opname mulai baris ke-20.")
                return render(request, 'exceltoexcel.html', {'results': results, 'summary': summary})

            system_file.seek(0)
            df_sys_raw = pd.read_excel(system_file, header=None)
        
            header_row_idx = 0
            for idx in range(len(df_sys_raw)):
                row_vals = [str(val).strip() for val in df_sys_raw.iloc[idx].values]
                if any('ItemFullName' in val for val in row_vals):
                    header_row_idx = idx
                    break

            system_file.seek(0)
            df_system = pd.read_excel(system_file, header=header_row_idx)
            df_system.columns = [str(col).strip() for col in df_system.columns]

            system_map = {}
            for _, row in df_system.iterrows():
                raw_name = row.get('ItemFullName')
                if pd.isna(raw_name) or str(raw_name).strip() == "":
                    continue
                
                name_str = str(raw_name).strip()
                parts = name_str.split(':', 2)
                if len(parts) >= 3:
                    item_name = parts[2].strip()  
                else:
                    item_name = name_str  

                def safe_float(val):
                    try:
                        return float(val) if not pd.isna(val) else 0.0
                    except:
                        return 0.0

                qoh = safe_float(row.get('QOH', 0))
                qoso = safe_float(row.get('QOSO', 0))
                qaqb = safe_float(row.get('QAQB', 0))
                qatota = safe_float(row.get('QATOTA', qoh + qoso + qaqb))

                system_map[item_name] = {
                    'qoh': int(qoh) if qoh.is_integer() else qoh,
                    'qoso': int(qoso) if qoso.is_integer() else qoso,
                    'qaqb': int(qaqb) if qaqb.is_integer() else qaqb,
                    'qatota': int(qatota) if qatota.is_integer() else qatota,
                }

            for name, excel_qty in opname_dict.items():
                sys_data = system_map.get(name, {'qoh': 0, 'qoso': 0, 'qaqb': 0, 'qatota': 0})
                
                qoh = sys_data['qoh']
                qoso = sys_data['qoso']
                qaqb = sys_data['qaqb']
                system_qty = sys_data['qatota']
                
                diff = system_qty - excel_qty 

                if diff < 0:
                    status = 'kurang'    
                    summary['kurang'] += 1
                elif diff > 0:
                    status = 'lebih'      
                    summary['lebih'] += 1
                else:
                    status = 'setara' 
                    summary['setara'] += 1

                results.append({
                    'item_name': name,
                    'excel_qty': excel_qty,
                    'qoh': qoh,
                    'qoso': qoso,
                    'qaqb': qaqb,
                    'system_qty': system_qty,
                    'diff': diff,
                    'status': status
                })

            summary['total'] = len(results)
            messages.success(request, f"Berhasil membandingkan {summary['total']} data berdasarkan File Opname.")

        except Exception as e:
            messages.error(request, f"Gagal memproses file Excel: {str(e)}")

    return render(request, 'exceltoexcel.html', {
        'results': results,
        'summary': summary
    })

def compare_exceltoexcelbogor(request):
    results = []
    summary = {'total': 0, 'kurang': 0, 'lebih': 0, 'setara': 0}

    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')      # File Excel Opname (Fisik)
        system_file = request.FILES.get('system_file')    # File Excel Sistem Bogor (Total)

        if not excel_file or not system_file:
            messages.error(request, "Harap unggah kedua file Excel (File Opname dan File Sistem Bogor).")
            return render(request, 'exceltoexcelbogor.html', {'results': results, 'summary': summary})

        try:
            excel_file.seek(0)
            df_opname = pd.read_excel(excel_file, header=None)
            
            opname_dict = {}
            start_row = 19  # Baris ke-20 di Excel

            for idx in range(start_row, len(df_opname)):
                val_b = df_opname.iloc[idx, 0]   # Kolom A (Nama Item)
                val_l = df_opname.iloc[idx, 11]  # Kolom L (Qty Fisik)

                if pd.isna(val_b) or str(val_b).strip() == "":
                    continue

                item_name = str(val_b).strip()
                try:
                    qty_excel = float(val_l) if not pd.isna(val_l) else 0.0
                    if qty_excel.is_integer():
                        qty_excel = int(qty_excel)
                except (ValueError, TypeError):
                    qty_excel = 0

                opname_dict[item_name] = qty_excel

            if not opname_dict:
                messages.warning(request, "Tidak ada data item ditemukan pada File Opname mulai baris ke-20.")
                return render(request, 'exceltoexcelbogor.html', {'results': results, 'summary': summary})

            system_file.seek(0)
            df_sys_raw = pd.read_excel(system_file, header=None)
            
            header_row_idx = 0
            for idx in range(len(df_sys_raw)):
                row_vals = [str(val).strip() for val in df_sys_raw.iloc[idx].values]
                if any('ItemFullName' in val for val in row_vals):
                    header_row_idx = idx
                    break

            system_file.seek(0)
            df_system = pd.read_excel(system_file, header=header_row_idx)
            df_system.columns = [str(col).strip() for col in df_system.columns]

            qty_col_name = None
            for col in df_system.columns:
                col_lower = col.lower()
                if any(k in col_lower for k in ['total', 'qatota', 'qty', 'quantity', 'jumlah']):
                    qty_col_name = col
                    break
            
            if not qty_col_name:
                numeric_cols = [c for c in df_system.columns if c != 'ItemFullName']
                if numeric_cols:
                    qty_col_name = numeric_cols[-1]

            system_map = {}
            for _, row in df_system.iterrows():
                raw_name = row.get('ItemFullName')
                if pd.isna(raw_name) or str(raw_name).strip() == "":
                    continue
                
                name_str = str(raw_name).strip()
                parts = name_str.split(':', 2)
                if len(parts) >= 3:
                    item_name = parts[2].strip()
                else:
                    item_name = name_str

                system_qty_val = 0.0
                if qty_col_name and qty_col_name in row:
                    try:
                        val = row[qty_col_name]
                        system_qty_val = float(val) if not pd.isna(val) else 0.0
                    except:
                        system_qty_val = 0.0

                if system_qty_val.is_integer():
                    system_qty_val = int(system_qty_val)

                system_map[item_name] = system_qty_val
                
            for name, excel_qty in opname_dict.items():
                system_qty = system_map.get(name, 0)
                
                # Data Opname dikurangi Data Sistem
                diff = excel_qty - system_qty

                if diff < 0:
                    status = 'kurang'    
                    summary['kurang'] += 1
                elif diff > 0:
                    status = 'lebih'      
                    summary['lebih'] += 1
                else:
                    status = 'setara' 
                    summary['setara'] += 1

                results.append({
                    'item_name': name,
                    'excel_qty': excel_qty,
                    'system_qty': system_qty,
                    'diff': diff,
                    'status': status
                })

            summary['total'] = len(results)
            messages.success(request, f"Berhasil membandingkan {summary['total']} data Bogor berdasarkan File Opname.")

        except Exception as e:
            messages.error(request, f"Gagal memproses file Excel Bogor: {str(e)}")

    return render(request, 'exceltoexcelbogor.html', {
        'results': results,
        'summary': summary
    })