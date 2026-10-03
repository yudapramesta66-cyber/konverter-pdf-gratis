import streamlit as st
import tempfile
import os
from pdf2docx import Converter
from PIL import Image
import pandas as pd

# --- KONFIGURASI ARSITEKTUR UI ---
st.set_page_config(page_title="Sistem Multi-Konverter", page_icon="🗂️", layout="centered")
st.title("Sistem Konversi Dokumen Terpadu 🚀")
st.write("Platform multi-format yang aman, gratis, dan efisien.")

# --- ROUTER (DISPATCHER) UI ---
# Menggunakan pola state-management untuk mengubah UI berdasarkan pilihan user
conversion_type = st.selectbox(
    "Pilih Jenis Konversi:",
    (
        "PDF ke Word (.docx)", 
        "Gambar (JPG/PNG) ke PDF", 
        "CSV ke Excel (.xlsx)", 
        "Excel (.xlsx) ke CSV"
    )
)

# Menyesuaikan filter uploader berdasarkan pilihan di atas
if conversion_type == "PDF ke Word (.docx)":
    accepted_types = ["pdf"]
elif conversion_type == "Gambar (JPG/PNG) ke PDF":
    accepted_types = ["png", "jpg", "jpeg"]
elif conversion_type == "CSV ke Excel (.xlsx)":
    accepted_types = ["csv"]
else:
    accepted_types = ["xlsx"]

# --- KOMPONEN INPUT ---
uploaded_file = st.file_uploader(f"Unggah file {accepted_types} Anda", type=accepted_types)

# --- FUNGSI-FUNGSI BISNIS (LOGIC LAYER) ---
# Pendekatan Clean Code: Setiap fungsi hanya melakukan SATU tugas spesifik (SOLID Principle)

def convert_pdf_to_docx(input_path, output_path):
    cv = Converter(input_path)
    cv.convert(output_path)
    cv.close()

def convert_image_to_pdf(input_path, output_path):
    image = Image.open(input_path)
    # Ubah mode ke RGB (karena PDF tidak mendukung format RGBA/Transparan secara langsung)
    rgb_image = image.convert('RGB')
    rgb_image.save(output_path)

def convert_csv_to_excel(input_path, output_path):
    df = pd.read_csv(input_path)
    df.to_excel(output_path, index=False, engine='openpyxl')

def convert_excel_to_csv(input_path, output_path):
    df = pd.read_excel(input_path)
    df.to_csv(output_path, index=False)

# --- CONTROLLER & EKSEKUSI ---
if uploaded_file is not None:
    # Validasi Skalabilitas: Cek batas memori 10MB
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("Keamanan Sistem: Ukuran file melebihi kapasitas maksimal (10MB) untuk mencegah server crash.")
    else:
        st.info(f"Memproses konversi {conversion_type}...")
        
        try:
            # 1. Alokasi Penyimpanan Sementara (Aman dari bentrok antar-user)
            file_ext = "." + uploaded_file.name.split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_input:
                tmp_input.write(uploaded_file.getvalue())
                input_path = tmp_input.name
            
            # 2. Routing Tujuan Output
            if conversion_type == "PDF ke Word (.docx)":
                output_ext = ".docx"
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif conversion_type == "Gambar (JPG/PNG) ke PDF":
                output_ext = ".pdf"
                mime_type = "application/pdf"
            elif conversion_type == "CSV ke Excel (.xlsx)":
                output_ext = ".xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                output_ext = ".csv"
                mime_type = "text/csv"
                
            output_path = input_path.replace(file_ext, output_ext)
            
            # 3. Dispatcher Logika Konversi
            if conversion_type == "PDF ke Word (.docx)":
                convert_pdf_to_docx(input_path, output_path)
            elif conversion_type == "Gambar (JPG/PNG) ke PDF":
                convert_image_to_pdf(input_path, output_path)
            elif conversion_type == "CSV ke Excel (.xlsx)":
                convert_csv_to_excel(input_path, output_path)
            else:
                convert_excel_to_csv(input_path, output_path)
            
            # 4. Penyiapan Unduhan
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
            
            # 5. Keamanan: Housekeeping (Pembersihan storage)
            os.remove(input_path)
            os.remove(output_path)
            
        except Exception as e:
            st.error(f"Kesalahan Sistem: File rusak atau format tidak kompatibel. Detail: {e}")