import streamlit as st
import tempfile
import os
from pdf2docx import Converter
from PIL import Image
import pandas as pd
import convertapi

# --- 1. KONFIGURASI ARSITEKTUR UI & KEAMANAN (GLOBAL) ---
st.set_page_config(page_title="Sistem Multi-Konverter", page_icon="🗂️", layout="centered")

# [REFACTORING ARSITEKTUR]: Manajemen Kredensial Global
# Menarik kunci rahasia di awal siklus hidup sistem untuk mencegah instansiasi NoneType pada library.
try:
    # Menggunakan fungsi str() untuk memaksa (Type Casting) nilai menjadi teks
    convertapi.api_secret = str(st.secrets["CONVERTAPI_SECRET"])
except (KeyError, FileNotFoundError):
    convertapi.api_secret = None # Dibiarkan kosong, akan ditangkap oleh fungsi logika di bawah

st.title("Sistem Konversi Dokumen Terpadu 🚀")
st.write("Platform multi-format berbasis Microservices yang aman, gratis, dan efisien.")
# --- MODUL DIAGNOSTIK KEAMANAN (DEBUGGING) ---
st.write("---")
st.markdown("### 🛠️ Mode Diagnostik Server")
if "CONVERTAPI_SECRET" in st.secrets:
    secret_val = str(st.secrets["CONVERTAPI_SECRET"])
    st.success("✅ Status: Kunci Rahasia BERHASIL TERDETEKSI di brankas server.")
    
    # Menampilkan hanya 4 karakter awal dan akhir untuk audit tanpa membocorkan kunci
    if len(secret_val) > 10:
        st.info(f"Audit Kunci Terbaca: {secret_val[:4]}••••••••••••••••{secret_val[-4:]}")
    else:
        st.warning("⚠️ Kunci terdeteksi, namun sepertinya format teks terlalu pendek (tidak valid).")
else:
    st.error("❌ Status: Kunci Rahasia TIDAK TERDETEKSI. Server buta terhadap konfigurasi Secrets Anda.")
st.write("---")

# --- 2. ROUTER (DISPATCHER) UI ---
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

# --- 3. FUNGSI BISNIS (LOGIC LAYER) ---

def convert_pdf_to_docx(input_path, output_path):
    cv = Converter(input_path)
    cv.convert(output_path)
    cv.close()

def convert_docx_to_pdf(input_path, output_path):
    """
    Integrasi API Pihak Ketiga (Microservice).
    Menerapkan Defensive Programming untuk memvalidasi ketersediaan Kunci Rahasia.
    """
    # Analisis Keamanan Lapisan 2: Memblokir eksekusi jika kunci tidak valid
    if not convertapi.api_secret or convertapi.api_secret == "None":
        raise ValueError("API Token tidak terbaca oleh sistem. Pastikan Anda telah mengklik 'Save changes' di menu Secrets Streamlit Cloud.")
    
    # Eksekusi HTTP Request ke server pihak ketiga
    result = convertapi.convert('pdf', {'File': input_path}, from_format='docx')
    result.save_files(output_path)

def convert_image_to_pdf(input_path, output_path):
    image = Image.open(input_path)
    rgb_image = image.convert('RGB')
    rgb_image.save(output_path)

def convert_csv_to_excel(input_path, output_path):
    df = pd.read_csv(input_path)
    df.to_excel(output_path, index=False, engine='openpyxl')

def convert_excel_to_csv(input_path, output_path):
    df = pd.read_excel(input_path)
    df.to_csv(output_path, index=False)

# --- 4. CONTROLLER & EKSEKUSI ---
if uploaded_file is not None:
    # Skalabilitas & Keamanan: Mencegah serangan memori (Denial of Service)
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("Gagal: Ukuran file melebihi kapasitas maksimal server (10MB).")
    else:
        st.info(f"Memproses {conversion_type}... Mohon tunggu.")
        
        try:
            # Manajemen File Sementara
            file_ext = "." + uploaded_file.name.split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_input:
                tmp_input.write(uploaded_file.getvalue())
                input_path = tmp_input.name
            
            # Penentuan Format Output
            if conversion_type == "PDF ke Word (.docx)":
                output_ext, mime_type = ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif conversion_type in ["Word (.docx) ke PDF", "Gambar (JPG/PNG) ke PDF"]:
                output_ext, mime_type = ".pdf", "application/pdf"
            elif conversion_type == "CSV ke Excel (.xlsx)":
                output_ext, mime_type = ".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                output_ext, mime_type = ".csv", "text/csv"
                
            output_path = input_path.replace(file_ext, output_ext)
            
            # Eksekusi Mesin Konversi
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
            
            # Persiapan Unduhan
            with open(output_path, "rb") as f:
                output_bytes = f.read()
                
            st.success("Konversi Berhasil! 🎉")
            
            final_filename = uploaded_file.name.rsplit('.', 1)[0] + output_ext
            st.download_button(
                label=f"Unduh File Anda",
                data=output_bytes,
                file_name=final_filename,
                mime=mime_type
            )
            
            # Manajemen Memori: Penghapusan File Fisik
            os.remove(input_path)
            os.remove(output_path)
            
        except ValueError as ve:
            st.error(f"Peringatan Keamanan: {ve}")
        except Exception as e:
            st.error(f"Kesalahan Sistem internal: {e}")
