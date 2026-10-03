import streamlit as st
import tempfile
import os
from pdf2docx import Converter
from PIL import Image
import pandas as pd
import convertapi

# --- 1. KONFIGURASI ARSITEKTUR UI ---
st.set_page_config(page_title="Sistem Multi-Konverter", page_icon="🗂️", layout="centered")
st.title("Sistem Konversi Dokumen Terpadu 🚀")
st.write("Platform multi-format berbasis Microservices yang aman, gratis, dan efisien.")

# --- 2. ROUTER (DISPATCHER) UI ---
# State management untuk filter ekstensi file dinamis
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
# Pendekatan SOLID: Setiap fungsi memiliki satu tanggung jawab spesifik

def convert_pdf_to_docx(input_path, output_path):
    cv = Converter(input_path)
    cv.convert(output_path)
    cv.close()

def convert_docx_to_pdf(input_path, output_path):
    """
    Integrasi API Pihak Ketiga (ConvertAPI).
    Mengambil kunci secara dinamis dari brankas server.
    """
    try:
        convertapi.api_secret = st.secrets["CONVERTAPI_SECRET"]
        # API Call ke server eksternal
        result = convertapi.convert('pdf', {'File': input_path}, from_format='docx')
        result.save_files(output_path)
    except KeyError:
        raise Exception("API Token tidak ditemukan di brankas sistem (Streamlit Secrets).")

def convert_image_to_pdf(input_path, output_path):
    image = Image.open(input_path)
    # Konversi ke RGB untuk mencegah error pada gambar berlatar transparan (RGBA)
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
    # Keamanan: Mencegah Memory Exhaustion (Batas 10MB)
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("Gagal: Ukuran file melebihi kapasitas maksimal (10MB).")
    else:
        st.info(f"Memproses {conversion_type}... Mohon tunggu.")
        
        try:
            # Alokasi penyimpanan sementara di server
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
            
            # Eksekusi rute konversi
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
            
            # Persiapan file untuk diunduh client
            with open(output_path, "rb") as f:
                output_bytes = f.read()
                
            st.success("Konversi Berhasil! 🎉")
            
            final_filename = uploaded_file.name.rsplit('.', 1)[0] + output_ext
            st.download_button(
                label=f"Unduh {final_filename}",
                data=output_bytes,
                file_name=final_filename,
                mime=mime_type
            )
            
            # Housekeeping: Hapus file fisik dari server
            os.remove(input_path)
            os.remove(output_path)
            
        except Exception as e:
            st.error(f"Kesalahan Sistem: {e}")
