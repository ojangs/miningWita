import pandas as pd
import streamlit as st
from streamlit import session_state
from fungsi3testing import Mining as mn
from fungsi3testing import PaketBundling as pb


class Interface:
    # Hal 1
    def halamanMasukkanFile():
        # Menampilkan judul yang rata tengah
        st.markdown(
            "<h1 >Selamat Datang di Sistem Rekomendasi Paket Bundling</h1>", unsafe_allow_html=True)
        st.divider()

        upload1 = mn.memasukkanTransaksi()
        mn.validasiMasukkanTransaksi(upload1)
        upload2 = mn.memasukkanKatalog()
        mn.validasiMasukkanKatalog(upload2)

        if st.button('Melihat Proses Mining', type="primary", use_container_width=True):
            if 'upload_transactions' in session_state and 'upload_katalog' in session_state:
                if not mn.getUploadTransaksi().empty and not mn.getUploadKatalog().empty:
                    session_state.selected_page = "Proses Mining"
                    st.rerun()
                elif mn.getUploadKatalog().empty and mn.getUploadTransaksi().empty:
                    st.error('Masukkan kedua file terlebih dahulu')
                elif mn.getUploadKatalog().empty:
                    st.error("Masukkan file katalog terlebih dahulu")
                elif mn.getUploadTransaksi().empty:
                    st.error("Masukkan file transaksi terlebih dahulu")

    def halamanProsesMining():
        st.markdown('<h1>Halaman Proses Mining</h1>', unsafe_allow_html=True)
        if not mn.getUploadTransaksi().empty and not mn.getUploadKatalog().empty:
            if 'proses_association_rule_done' not in session_state:
                session_state.proses_association_rule_done = False
            df_transaksi = mn.getUploadTransaksi()
            df_katalog = mn.getUploadKatalog()
            cleaned_data = mn.cleaning(df_transaksi,df_katalog)
            merged_data = mn.merging(cleaned_data,df_katalog)
            mn.createListProduk(merged_data)
            transformedData = mn.transformData(merged_data)
            mn.rules(transformedData,merged_data)
            session_state.proses_association_rule_done = True
            mn.tampilProsesMining()
            if st.button("Memilih Kombinbasi Jenis", use_container_width=True, type="primary",):
                session_state.selected_page = 'MemilihKombinasiJenis'
                st.rerun()
        else:
            if mn.getUploadKatalog().empty and mn.getUploadTransaksi().empty:
                st.error('Masukkan kedua file terlebih dahulu')
            if mn.getUploadKatalog().empty and not mn.getUploadTransaksi().empty:
                st.error("Masukkan file katalog terlebih dahulu")
            if mn.getUploadTransaksi().empty and not mn.getUploadKatalog().empty:
                st.error("Masukkan file transaksi terlebih dahulu")

    def halamanMemilihKombinasiJenis():
        st.markdown('<h2>REKOMENDASI KOMBINASI JENIS</h2>', unsafe_allow_html=True)
        if not mn.getUploadTransaksi().empty and not mn.getUploadKatalog().empty:
            if session_state.proses_association_rule_done:   
                if 'rules' in session_state:
                    if mn.memeriksaRules() and not session_state.list_produk.empty:
                        mn.tampilHasilMining()
                        baris = mn.pilihRules()                   
                        selected_rules = mn.selected_rules(baris)
                        # pb.cari_Kombinasi(selected_rules,list_produk)
                        if st.button("Tampilkan Rekomendasi Paket", use_container_width=True, type="primary",):
                            list_produk = session_state.list_produk
                            pb.cari_Kombinasi(selected_rules,list_produk)
                            session_state.selected_page = 'HasilPaket'
                            st.rerun()
                    else:
                        st.error('Tidak Ada Rekomendasi Kombinasi Jenis, Silahkan Ganti File Transaksi dengan Periode Waktu yang berbeda')
            else:
                st.error('Proses Mining Belum dilakukan, silahkan pindah ke halaman melihat proses mining terlebih dahulu')
        else:
            if mn.getUploadKatalog().empty and mn.getUploadTransaksi().empty:
                st.error('Masukkan kedua file terlebih dahulu')
            if mn.getUploadKatalog().empty and not mn.getUploadTransaksi().empty:
                st.error("Masukkan file katalog terlebih dahulu")
            if mn.getUploadTransaksi().empty and not mn.getUploadKatalog().empty:
                st.error("Masukkan file transaksi terlebih dahulu")
    
    def halamanHasilPaketBundling():
        st.markdown('<h2>REKOMENDASI PAKET BUNDLING</h2>',unsafe_allow_html=True)
        if 'df_transactions' in session_state and 'df_katalog' in session_state:
            if 'proses_association_rule_done' in session_state:   
                if mn.memeriksaRules():
                    if 'selected_rules' in session_state:
                        if 'df_kombinasi' in session_state:
                            df_download = pd.DataFrame(session_state.df_kombinasi)
                            pb.tampilRekomendasiBundling()
                            if not session_state.df_kombinasi.empty:
                                pb.menyimpanDataPaketBundling(df_download)
                        if st.button('Ganti Kombinasi Jenis'):
                            mn.setJenis(pd.DataFrame(),pd.DataFrame())
                            session_state.selected_page = 'MemilihKombinasiJenis'
                            st.rerun()
                    else:
                        st.error('Silahkan Memilih Kombinasi Jenis Terlebih Dahulu ')
                else:
                    st.error('Tidak Ada Rekomendasi Kombinasi Jenis, Silahkan Ganti File Transaksi dengan Periode Waktu yang berbeda')
         
        elif 'df_transactions' not in session_state and 'df_katalog' not in session_state: 
            st.error('Masukkan Kedua File Terlebih Dahulu')
        elif 'df_transactions' not in session_state and 'df_katalog' in session_state: 
            st.error('Masukkan file transaksi terlebih dahulu')
        elif 'df_transactions' in session_state and 'df_katalog' not in session_state: 
            st.error('Masukkan file katalog terlebih dahulu')

    def halamanBuatBundling():
        paket = pb.buatpaketBundling(session_state.selected_rules,session_state.list_produk)
        pb.lihatpaketBundling(paket)
           
        #     if st.button('Lihat Hasil Paket Bundling',type='primary'):
        #         session_state.selected_page = 'HasilPaket'
        #         st.rerun()

        

class Main():
    def main():
        if 'selected_page' not in session_state:
                session_state.selected_page = 'Masukkan File'

        st.sidebar.title("Navigasi")
        ui = Interface
        pages = {
            "Masukkan File": ui.halamanMasukkanFile,
            "Proses Mining": ui.halamanProsesMining,
            "MemilihKombinasiJenis": ui.halamanMemilihKombinasiJenis,
            "HasilPaket": ui.halamanHasilPaketBundling,
            "BuatPaketBundling": ui.halamanBuatBundling
        }

        # Display buttons for each page in the sidebar
        selected_page = st.sidebar.button("Masukkan File", use_container_width=True)
        if selected_page:
            session_state.selected_page = "Masukkan File"

        selected_page = st.sidebar.button("Melihat Proses Mining", use_container_width=True)
        if selected_page:
            session_state.selected_page = "Proses Mining"

        selected_page = st.sidebar.button("Memilih Kombinasi Jenis", use_container_width=True)
        if selected_page:
            session_state.selected_page = "MemilihKombinasiJenis"

        # selected_page = st.sidebar.button("Hasil Paket", use_container_width=True)
        # if selected_page:
        #     session_state.selected_page = "HasilPaket"

        # Execute the selected page function
        pages[session_state.selected_page]()

if __name__ == "__main__":
    Main.main()
