import streamlit as st
import tempfile
import os
import requests  # Menggantikan import convertapi
import base64    # Untuk membaca hasil konversi dari JSON
from pdf2docx import Converter
from PIL import Image
import pandas as pd

# ... (Biarkan konfigurasi UI dan Router tetap sama seperti sebelumnya) ...

def convert_docx_to_pdf(input_path, output_path):
    """
    Integrasi API Pihak Ketiga (Direct REST API).
    Menggunakan HTTP POST murni untuk menghindari bug pada pustaka bawaan.
    """
    # Menarik Kunci Rahasia dari Brankas
    secret = str(st.secrets["CONVERTAPI_SECRET"])
    url = "https://v2.convertapi.com/convert/docx/to/pdf"
    
    # Merakit Header Otorisasi standar
    headers = {
        "Authorization": f"Bearer {secret}"
    }
    
    # Membaca file fisik dan mengirimkannya melalui jalur aman (multipart/form-data)
    with open(input_path, 'rb') as f:
        files = {'File': f}
        response = requests.post(url, headers=headers, files=files)
    
    # Validasi Skalabilitas & Error Handling
    if response.status_code == 200:
        # Mengurai JSON response dan mendekode file PDF dari format Base64
        data = response.json()
        file_b64 = data['Files'][0]['FileData']
        with open(output_path, 'wb') as f_out:
            f_out.write(base64.b64decode(file_b64))
    else:
        # Menangkap pesan error spesifik jika API menolak permintaan
        raise Exception(f"Server ConvertAPI menolak permintaan. Kode: {response.status_code}, Detail: {response.text}")

# ... (Biarkan sisa kode Controller & Eksekusi di bawahnya tetap sama) ...
