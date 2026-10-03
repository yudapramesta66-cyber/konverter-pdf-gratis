import streamlit as st
import tempfile
import os
import requests
import base64
from pdf2docx import Converter
from PIL import Image
import pandas as pd

# ==========================================
# 1. KONFIGURASI ARSITEKTUR UI & KEAMANAN
# ==========================================
st.set_page_config(page_title="Sistem Multi-Konverter", page_icon="🗂️", layout="centered")

st.title("Sistem Konversi Dokumen Terpadu 🚀")
st.write("Platform multi-format berbasis Microservices yang aman, gratis, dan efisien.")

# ==========================================
# 2. ROUTER (DISPATCHER) UI
# ==========================================
# Menerapkan State Management untuk memfilter ekstensi file secara dinamis
conversion_type = st.selectbox(
    "Pilih Jenis Konversi:",
    (
        "PDF ke Word (.docx)", 
        "Word (.docx) ke PDF", 
        "Gambar (JPG/PNG) ke PDF", 
        "CSV ke Excel (.xlsx)", 
        "Excel (.xlsx) ke CSV"
    )
)

if conversion_type == "PDF ke Word (.docx)":
    accepted_types = ["pdf"]
elif conversion_type == "Word (.docx) ke PDF":
    accepted_types = ["docx"]
elif conversion_type == "Gambar (JPG/PNG) ke PDF":
    accepted_types = ["png", "jpg", "jpeg"]
elif conversion_type == "CSV ke Excel (.xlsx)":
    accepted_types = ["csv"]
else:
    accepted_types = ["xlsx"]

uploaded_file = st.file_uploader(f"Unggah file Anda (Format: {', '.join(accepted_types)})", type=accepted_types)

# ==========================================
# 3. FUNGSI BISNIS (LOGIC LAYER)
# ==========================================
# Pendekatan Clean Code: Setiap fungsi menangani tepat satu jenis konversi

def convert_pdf_to_docx(input_path, output_path):
    cv = Converter(input_path)
    cv.convert(output_path)
    cv.close()

def convert_docx_to_pdf(input_path, output_path):
    """
    Integrasi API Pihak Ketiga (Direct REST API).
    Menggunakan modul requests HTTP POST murni untuk stabilitas maksimum.
    """
    # Defensive Programming: Validasi eksistensi kunci rahasia dari brankas server
    try:
        api_secret = str(st.secrets["CONVERTAPI_SECRET"])
    except (KeyError, FileNotFoundError):
        raise ValueError("API Token tidak ditemukan di brankas server. Silakan cek menu Secrets di Streamlit Cloud.")
    
    # Endpoint REST API ConvertAPI
    url = "https://v2.convertapi.com/convert/docx/to/pdf"
    
    # Headers untuk otorisasi standar industri (OAuth 2.0 style)
    headers = {
        "Authorization": f"Bearer {api_secret}"
    }
    
    # Membaca file fisik untuk dikirim via form-data
    with open(input_path, 'rb') as f:
        files = {'File': f}
        # Eksekusi pengiriman file ke server eksternal
        response = requests.post(url, headers=headers, files=files)
    
    # Error Handling & Payload Decoding
    if response.status_code == 200:
        data = response.json()
        file_b64 = data['Files'][0]['FileData']
        
        # Dekode string Base64 kembali menjadi file fisik (PDF)
        with open(output_path, 'wb') as f_out:
            f_out.write(base64.b64decode(file_b64))
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")

def convert_image_to_pdf(input_path, output_path):
    image = Image.open(input_path)
    # Konversi ke profil RGB untuk mencegah crash pada gambar RGBA (latar transparan)
    rgb_image = image.convert('RGB')
    rgb_image.save(output_path)

def convert_csv_to_excel(input_path, output_path):
    df = pd.read_csv(input_path)
    df.to_excel(output_path, index=False, engine='openpyxl')

def convert_excel_to_csv(input_path, output_path):
    df = pd.read_excel(input_path)
    df.to_csv(output_path, index=False)

# ==========================================
# 4. CONTROLLER & EKSEKUSI (APPLICATION LAYER)
# ==========================================
if uploaded_file is not None:
    # Skalabilitas Keamanan: Blokir file > 10MB untuk mencegah Memory Exhaustion (DDoS protection level 1)
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("Gagal: Ukuran file melebihi kapasitas maksimal server (10MB).")
    else:
        st.info(f"Memproses {conversion_type}... Mohon tunggu.")
        
        try:
            # Manajemen File Sementara (Mengamankan I/O disk)
            file_ext = "." + uploaded_file.name.split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_input:
                tmp_input.write(uploaded_file.getvalue())
                input_path = tmp_input.name
            
            # Penentuan meta-data output
            if conversion_type == "PDF ke Word (.docx)":
                output_ext, mime_type = ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif conversion_type in ["Word (.docx) ke PDF", "Gambar (JPG/PNG) ke PDF"]:
                output_ext, mime_type = ".pdf", "application/pdf"
            elif conversion_type == "CSV ke Excel (.xlsx)":
                output_ext, mime_type = ".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                output_ext, mime_type = ".csv", "text/csv"
                
            output_path = input_path.replace(file_ext, output_ext)
            
            # Eksekusi Fungsi Konversi (Routing)
            if conversion_type == "PDF ke Word (.docx)":
                convert_pdf_to_docx(input_path, output_path)
            elif conversion_type == "Word (.docx) ke PDF":
                convert_docx_to_pdf(input_path, output_path)
            elif conversion_type == "Gambar (JPG/PNG) ke PDF":
                convert_image_to_pdf(input_path, output_path)
            elif conversion_type == "CSV ke Excel (.xlsx)":
                convert_csv_to_excel(input_path, output_path)
            else:
                convert_excel_to_csv(input_path, output_path)
            
            # Persiapan file untuk dikirim (Download)
            with open(output_path, "rb") as f:
                output_bytes = f.read()
                
            st.success("Konversi Berhasil! 🎉")
            
            # Konstruksi nama file akhir
            final_filename = uploaded_file.name.rsplit('.', 1)[0] + output_ext
            
            st.download_button(
                label=f"Unduh {final_filename}",
                data=output_bytes,
                file_name=final_filename,
                mime=mime_type
            )
            
            # Pembersihan Memori (Garbage Collection): Menghapus file fisik setelah dimuat ke RAM
            os.remove(input_path)
            os.remove(output_path)
            
        except ValueError as ve:
            st.error(f"Peringatan Keamanan: {ve}")
        except Exception as e:
            st.error(f"Kesalahan Sistem: {e}")
            # Failsafe pembersihan jika terjadi error di tengah jalan
            if os.path.exists(input_path): os.remove(input_path)
            if 'output_path' in locals() and os.path.exists(output_path): os.remove(output_path)
