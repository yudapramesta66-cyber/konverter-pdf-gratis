import streamlit as st
from pdf2docx import Converter
import tempfile
import os

# --- PENGATURAN UI & UX ---
st.set_page_config(page_title="Konverter PDF Gratis", page_icon="📄", layout="centered")

st.title("Sistem Konversi Dokumen 🚀")
st.write("Aplikasi sederhana untuk mengubah file PDF menjadi Microsoft Word (.docx) secara gratis dan aman.")

# --- KOMPONEN INPUT ---
uploaded_file = st.file_uploader("Silakan unggah file PDF Anda", type=["pdf"])

# --- LOGIKA VALIDASI & PROSES ---
if uploaded_file is not None:
    st.success(f"File '{uploaded_file.name}' berhasil diterima sistem!")
    
    # Validasi ukuran file (Max 10 MB)
    file_size = uploaded_file.size
    if file_size > 10 * 1024 * 1024:
        st.error("Gagal: Ukuran file melebihi batas 10MB.")
    else:
        st.info("Memulai proses konversi... Mohon tunggu sebentar.")
        
        # --- BLOK EKSEKUSI KONVERSI ---
        try:
            # 1. Buat file sementara (Temporary File) yang aman untuk PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(uploaded_file.getvalue())
                pdf_path = tmp_pdf.name
            
            # 2. Tentukan nama dan lokasi file hasil (.docx)
            docx_path = pdf_path.replace(".pdf", ".docx")
            
            # 3. Mesin Konversi Bekerja
            cv = Converter(pdf_path)
            cv.convert(docx_path)
            cv.close()
            
            # 4. Baca hasil konversi ke dalam memori untuk tombol unduh
            with open(docx_path, "rb") as docx_file:
                docx_bytes = docx_file.read()
                
            st.success("Konversi Berhasil! 🎉")
            
            # 5. Tampilkan Tombol Unduh
            st.download_button(
                label="Unduh File Word (.docx)",
                data=docx_bytes,
                file_name=uploaded_file.name.replace(".pdf", ".docx"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            # 6. Housekeeping: Hapus file dari server agar tidak memakan storage
            os.remove(pdf_path)
            os.remove(docx_path)
            
        except Exception as e:
            # Menangkap dan menampilkan error jika file rusak atau tidak bisa diproses
            st.error(f"Terjadi kesalahan saat mengonversi file: {e}")