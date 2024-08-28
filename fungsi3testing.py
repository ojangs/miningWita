import streamlit as st
from streamlit import session_state
import pandas as pd
import math
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import association_rules, fpgrowth
import itertools
from io import BytesIO

class Mining:
    def MemeriksaUploadTransaksi():
        # Initialize the session_state dictionary if it doesn't exist
        if 'upload_transactions' not in st.session_state:
            session_state.upload_transactions = None
        if 'df_transactions' not in st.session_state:
            session_state.df_transactions = pd.DataFrame()
            
        # Memeriksa apakah 'upload_transactions' tidak kosong dan DataFrame 'df_transactions' tidak kosong
        return session_state.get('upload_transactions') is not None and not session_state.df_transactions.empty
     
    def setUploadTransaksi(newUploadTransaction, newDFTransactions):
        session_state.upload_transactions = newUploadTransaction
        session_state.df_transactions = newDFTransactions

    def getUploadTransaksi():
        if Mining.MemeriksaUploadTransaksi():
            return session_state.df_transactions
        return pd.DataFrame()
    
    def memasukkanTransaksi():
        if Mining.getUploadTransaksi().empty:
            # File uploader
            st.markdown("<h4>Masukkan File Transaksi Penjualan</h4>", unsafe_allow_html=True)
            upload = st.file_uploader("Choose an Excel file", type="xlsx")
            return upload
        else:
            st.success("File Berhasil dimasukkan")
            if st.button("Ganti data transaksi"):
                Mining.setUploadTransaksi(None, None)
                st.rerun()

    def validasiMasukkanTransaksi(file):
        if file:
            dataframe_transaction = pd.read_excel(file) 
            # Mengecek apakah kolom yang dibutuhkan ada di DataFrame
            required_columns = ['Faktur', 'Nama Barang', 'Qty']
            missing_columns = [col for col in required_columns if col not in dataframe_transaction.columns]
            if len(missing_columns) == 0:
                Mining.setUploadTransaksi(file, dataframe_transaction)
                st.rerun()
            else:
                st.error("File tidak valid")

    def MemeriksaUploadKatalog():
        # Initialize the session_state dictionary if it doesn't exist
        if 'upload_katalog' not in st.session_state:
            session_state.upload_katalog = None
        if 'df_katalog' not in st.session_state:
            session_state.df_katalog = pd.DataFrame()
            
        # Memeriksa apakah 'upload_transactions' tidak kosong dan DataFrame 'df_transactions' tidak kosong
        return session_state.get('upload_katalog') is not None and not session_state.df_katalog.empty
     
    def setUploadKatalog(newUploadKatalog, newDFKatalog):
        session_state.upload_katalog = newUploadKatalog
        session_state.df_katalog = newDFKatalog

    def setJenis(newSelectedRules,newDfKombinasi):
        session_state.selected_rules = newSelectedRules
        session_state.df_kombinasi = newDfKombinasi 

    def getUploadKatalog():
        if Mining.MemeriksaUploadKatalog():
            return session_state.df_katalog
        return pd.DataFrame()
    
    def memasukkanKatalog():
        if Mining.getUploadKatalog().empty:
            # File uploader
            st.markdown("<h4>Masukkan File Katalog</h4>", unsafe_allow_html=True)
            upload = st.file_uploader("Choose an Excel file", key='katalog',type="xlsx")
            return upload
        else:
            st.success("File Berhasil dimasukkan")
            if st.button("Ganti file katalog", key='katalog'):
                Mining.setUploadKatalog(None, None)
                st.rerun()

    def validasiMasukkanKatalog(file):
        if file:
            dataframe_katalog = pd.read_excel(file) 
            # Mengecek apakah kolom yang dibutuhkan ada di DataFrame
            required_columns = ['Description', 'Jenis', 'Harga Jual', 'ket']
            missing_columns = [col for col in required_columns if col not in dataframe_katalog.columns]
            if len(missing_columns) == 0:
                Mining.setUploadKatalog(file, dataframe_katalog)
                st.rerun()
            else:
                st.error("File tidak valid")

    
    def cleaning(fileTransaksi,fileKatalog):
        katalog = fileKatalog.copy()
        transaksi = fileTransaksi.copy()
        bundling_items = katalog[(katalog['ket'] != 'Bukan Oleh-Oleh') & (katalog['Harga Jual'] >= 10000)]['Description']
        filtered_data1 = transaksi[transaksi['Nama Barang'].isin(bundling_items)]
        return filtered_data1
    
    
    def merging(filtered_data1,fileKatalog):
        filterdata = filtered_data1.copy()
        katalog = fileKatalog.copy()
        merged_data = pd.merge(filterdata, katalog, left_on='Nama Barang', right_on='Description')
        return merged_data
    
    
    def createListProduk(merged_Data):
        if 'list_produk' not in session_state:
            session_state.list_produk = None
        list_produk = merged_Data.copy()
        list_produk_per_jenis = list_produk.groupby(['Jenis', 'Nama Barang']).agg({
            'Qty': 'sum',
            'Harga Beli': 'first',
            'Harga Jual': 'first'
        }).reset_index()
        list_produk_per_jenis = list_produk_per_jenis.reset_index(drop=True)
        list_produk_per_jenis['No'] = list_produk_per_jenis.index + 1
        list_produk_per_jenis['No'] = list_produk_per_jenis['No'].astype(str)
        list_produk_per_jenis.set_index('No',inplace=True)
        session_state.list_produk = list_produk_per_jenis
        return list_produk_per_jenis

    
    def transformData(merged_data):
        if 'te_data' not in session_state:
            session_state.te_data = pd.DataFrame()
        data = merged_data.copy()
        transactions = data.groupby('Faktur')['Jenis'].apply(lambda x: list(set(x))).tolist()
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        te_encode = pd.DataFrame(te_ary, columns=te.columns_)
        session_state.te_data = te_encode
        return te_encode
    
    def memeriksaRules():
        rules_df = session_state.get('rulesvalid4max')
        return rules_df is not None and not rules_df.empty
    
    
    def rules(te_encode,mergeData):
        min_confidence = 0.7
        findminSup = mergeData.copy()
        minSup = findminSup.groupby('Faktur')['Jenis'].apply(lambda x: list(set(x))).tolist()
        meanKemunculanJenis = sum(len(transaction)for transaction in minSup)/len(minSup)
        roundedminSup = math.ceil(meanKemunculanJenis)/len(minSup)
        
        if 'rules' not in session_state:
            session_state.rules = None

        if 'rulesvalid' not in session_state:
            session_state.rulesvalid = None

        if 'rulesvalid4max' not in session_state:
            session_state.rulesvalid4max = None

        if 'frequent_itemsets' not in session_state:
            session_state.frequent_itemsets = pd.DataFrame()

        if 'df_association' not in session_state:
            session_state.df_association = pd.DataFrame()

        if 'df_association_unique' not in session_state:
            session_state.df_association_unique = pd.DataFrame()
        

        frequent_itemsets = fpgrowth(te_encode, min_support=roundedminSup, use_colnames=True)
        frequent_itemsets = frequent_itemsets[frequent_itemsets['itemsets'].apply(lambda x: all(item.strip() != '' for item in x))]
        session_state.frequent_itemsets = frequent_itemsets

        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        rules['Count jenis'] = rules['antecedents'].apply(lambda x: len(x)) + rules['consequents'].apply(lambda x: len(x))
        rules['id_rule'] = rules.reset_index().index + 1
        session_state.rules = rules
        rulesValid = pd.DataFrame(rules[rules['lift'] > 1])
        session_state.rulesvalid = rulesValid
        rulesValid4max = pd.DataFrame(rulesValid[rulesValid['Count jenis'] <= 4])
        session_state.rulesvalid4max = rulesValid4max

        df_association = rulesValid4max.copy()  
        df_association = df_association.sort_values(by='lift', ascending=False,ignore_index=True)  
        df_association['Jenis Produk'] = [sorted(list(row['antecedents']) + list(row['consequents'])) for _, row in df_association.iterrows()]
        df_association.drop(columns=['id_rule','antecedents', 'consequents', 'antecedent support', 'consequent support', 'support', 'confidence', 'lift', 'leverage','conviction', 'zhangs_metric', 'Count jenis'], inplace=True)
        session_state.df_association = df_association
        
        df_association_unique = df_association.copy()
        df_association_unique['Jenis Produk'] = df_association_unique['Jenis Produk'].astype(str)
        df_association_unique = df_association_unique.drop_duplicates(subset='Jenis Produk')
        df_association_unique['Jenis Produk'] = df_association_unique['Jenis Produk'].apply(eval)
        df_association_unique = df_association_unique.reset_index(drop=True)
        df_association_unique['No'] = df_association_unique.index + 1
        df_association_unique['No'] = df_association_unique['No'].astype(str)
        df_association_unique.set_index('No', inplace=True)
        session_state.df_association_unique = df_association_unique

        return df_association_unique,frequent_itemsets

    
    def pilihRules():
        if 'df_association_unique' in session_state:
            baris = st.number_input('Pilih Kombinasi Jenis Berdasarkan No Baris',min_value=1, max_value=len(session_state.df_association_unique), step=1,key='baris')
            return baris   
    
    def selected_rules(baris):
        if 'selected_rules' not in session_state:
            session_state.selected_rules = pd.DataFrame()
        selected_rules_df = session_state.df_association_unique.loc[str(baris),'Jenis Produk']
        session_state.selected_rules = selected_rules_df
        return selected_rules_df

    def tampilHasilMining():      
        st.dataframe(session_state.df_association_unique,use_container_width=True)
        with st.expander('Tampilkan List Produk'):
            st.dataframe(session_state.list_produk,use_container_width=True)

    
    def tampilProsesMining():
        # MENAMPILKAN DATA TRANSAKSI
        df_transactions = Mining.getUploadTransaksi()
        st.markdown("<h2>Data Transaksi</h2>",unsafe_allow_html=True)
        st.write("Terdapat: ", df_transactions.shape[0], "record dan", df_transactions.shape[1], "attribute")
        st.dataframe(df_transactions,use_container_width=True)
        st.divider()

        # MENAMPILKAN DATA KATALOG
        df_katalog = Mining.getUploadKatalog()
        st.markdown("<h2>Data Katalog</h2>",unsafe_allow_html=True)
        st.write("Terdapat: ", df_katalog.shape[0], "record dan", df_katalog.shape[1], "attribute")
        st.dataframe(df_katalog,use_container_width=True)
        st.divider()  
        
        # MENAMPILKAN PRAPOESES
        st.markdown("<h2>Menampilkan PRAPROSES</h2>",unsafe_allow_html=True)
        # CLEANING
        st.markdown("<h3>Cleaning Data</h3>",unsafe_allow_html=True)
        st.markdown("<p>Menghapus produk bukan oleh - oleh pada data transaksi </p>",unsafe_allow_html=True)
        with st.expander('Tampilkan Produk Bukan Oleh - oleh'):
            dataNonOleh2 = df_katalog[df_katalog['ket'] == 'Bukan Oleh-Oleh']['Description']
            dataNonOleh2 = dataNonOleh2.reset_index(drop=True)
            st.dataframe(dataNonOleh2,use_container_width=True)
        cleaned_Data = Mining.cleaning(df_transactions,df_katalog)
        st.dataframe(cleaned_Data,use_container_width=True)
        # MERGING
        st.markdown("<h3>Merging</h3>",unsafe_allow_html=True)
        st.markdown("<p>Data tranasaksi yang telah dilakukan proses cleaning akan digabungkan dengan data katalog </p>",unsafe_allow_html=True)
        merged_Data = Mining.merging(cleaned_Data,df_katalog)
        st.dataframe(merged_Data,use_container_width=True)
        # TRANSFORMASI DATA
        st.markdown("<h3>TRANSFORMASI</h3>",unsafe_allow_html=True)
        st.markdown("<p>Data Akan ditransformasi untuk dimasukkan kedalam model </p>",unsafe_allow_html=True)
        transactionsList = merged_Data.groupby('Faktur')['Jenis'].apply(lambda x: list(set(x))).tolist()
        transformedData = Mining.transformData(merged_Data)
        st.markdown("<p>List Jenis Item Per Transaksi </p>",unsafe_allow_html=True)
        st.dataframe(transactionsList,use_container_width=True)
        st.markdown("<p>Data Akan ditransformasi untuk dimasukkan kedalam model </p>",unsafe_allow_html=True)
        st.dataframe(transformedData,use_container_width=True)

        # MENAMPILKAN PROSES MODELLING
        st.markdown('<h2> PROSES MODELLING</h2>',unsafe_allow_html=True)
        st.markdown('<h3> Menentukkan nilai Minimum Support</h3>',unsafe_allow_html=True)
        st.markdown('<p> nilai Minimum Support Didapatkan dari rata - rata kemunculan jenis item pada seluruh transaksi </p>',unsafe_allow_html=True)
        minSup = merged_Data.groupby('Faktur')['Jenis'].apply(lambda x: list(set(x))).tolist()
        meanKemunculanJenis = sum(len(transaction)for transaction in minSup)/len(minSup)
        st.write("minimum support = {}".format(meanKemunculanJenis))
        roundedminSup = math.ceil(meanKemunculanJenis)
        st.markdown('<p> Lalu nilai tersebut akan dibulatkan ke atas </p>',unsafe_allow_html=True)
        st.write("Dibulatkan menjadi = {}".format(roundedminSup))
        # MENAMPILKAN MODELING MIN CONFIDENCE
        st.markdown(
            "<h3 >Minimum Confidence</h3>", unsafe_allow_html=True)
        st.markdown(
            "<p >nilai minimum confidence ditetapkan 60 persen berdasarkan referensi penelitian</p>", unsafe_allow_html=True)
        min_confidence = 0.6
        st.write(min_confidence)
        #  MENAMPILKAN Frequent itemsets
        st.markdown("<h3>Menampilkan Frequent Itemset</h3>", unsafe_allow_html=True)
        df_fp = pd.DataFrame(session_state.frequent_itemsets)
        st.dataframe(df_fp, use_container_width=True)
        #  MENAMPILKAN Aturan asosiasi
        st.markdown("<h3>Menampilkan Aturan asosiasi terbentuk</h3>", unsafe_allow_html=True)
        df_rule = pd.DataFrame(session_state.rules)
        st.dataframe(df_rule, use_container_width=True)
        #  MENAMPILKAN Aturan asosiasi yang valid
        st.markdown("<h3>Menampilkan Aturan asosiasi yang valid</h3>", unsafe_allow_html=True)
        st.markdown(
            "<p>aturan Asosiasi yang valid merupakan aturan asosiasi yang memiliki nilai Lift Ratio lebih dari satu</p>", unsafe_allow_html=True)
        df_rule_valid = pd.DataFrame(session_state.rulesvalid)
        st.dataframe(df_rule_valid, use_container_width=True)
        #  MENAMPILKAN Aturan asosiasi 4 max kombinasi
        st.markdown("<h3>Menampilkan Aturan asosiasi yang memiliki jumlah kombinasi tidak lebih dari 4</h3>", unsafe_allow_html=True)
        df_rule4vlaid = session_state.df_association
        st.dataframe(df_rule4vlaid, use_container_width=True)
        #  MENAMPILKAN aturan asosisai 4 max kombinsai no duplikat
        st.markdown("<h3>Hasil Penghapusan Duplikasi Aturan Asosiasi</h3>", unsafe_allow_html=True)
        df_rule4vlaid_unique = session_state.df_association_unique
        st.dataframe(df_rule4vlaid_unique, use_container_width=True)


class PaketBundling:
    
    def cari_Kombinasi(rules_terpilih, list_produk):
        if 'df_kombinasi' not in session_state:
            session_state.df_kombinasi = pd.DataFrame()
        if 'filter_list_produk' not in session_state:
            session_state.filter_list_produk = pd.DataFrame()
        # Filter produk berdasarkan jenis yang dipilih
        listProduk = list_produk.copy()
        listProdukTerpilih = listProduk[listProduk['Jenis'].isin(rules_terpilih)]
        listProdukTerpilih['Harga Beli'] = pd.to_numeric(listProdukTerpilih['Harga Beli'], errors='coerce')
        listProdukTerpilih['Harga Jual'] = pd.to_numeric(listProdukTerpilih['Harga Jual'], errors='coerce')

        # Drop rows with NaN values in 'Harga Beli' or 'Harga Jual'
        listProdukTerpilih = listProdukTerpilih.dropna(subset=['Harga Beli', 'Harga Jual'])
        tampilProduk_df = pd.DataFrame(listProdukTerpilih)
        tampilProduk_df = tampilProduk_df.reset_index(drop=True)
        tampilProduk_df.index = tampilProduk_df.index + 1
        session_state.filter_list_produk = tampilProduk_df
        listProdukTerpilih['Selisih'] = listProdukTerpilih['Harga Jual'] - listProdukTerpilih['Harga Beli']
        listProdukTerpilih = listProdukTerpilih[listProdukTerpilih['Selisih'] >= 5000]
        barang_laku = listProdukTerpilih[listProdukTerpilih['Qty'] >= 75]['Nama Barang'].unique()
        barang_tidak_laku = listProdukTerpilih[listProdukTerpilih['Qty'] < 75]['Nama Barang'].unique()

        nama_barang_terpilih = list(barang_laku) + list(barang_tidak_laku)

        if not barang_laku.size or not barang_tidak_laku.size:
            print("Tidak ada kombinasi yang memenuhi kriteria.")
            return pd.DataFrame(columns=['No', 'Nama Barang', 'Harga Bundling', 'Keuntungan'])
        # nama_barang_terpilih = listProdukTerpilih['Nama Barang'].unique()
        
        # Menentukan jumlah jenis
        num_jenis = len(rules_terpilih)
        columns = [f'Nama Barang {i+1}' for i in range(num_jenis)]
        
        # Membuat kombinasi produk
        kombinasi_produk = list(itertools.combinations(nama_barang_terpilih, num_jenis))
        
        # Menghapus duplikat urutan
        unique_cart_product = [tuple(sorted(item)) for item in kombinasi_produk]
        unique_cart_product = list(set(unique_cart_product))
        
        # Menghapus kombinasi dengan produk dari jenis yang sama
        def has_same_jenis(combination):
            jenis_list = [listProduk[listProduk['Nama Barang'] == item]['Jenis'].values[0] for item in combination]
            return len(jenis_list) != len(set(jenis_list))
        
        unique_cart_product = [item for item in unique_cart_product if not has_same_jenis(item)]

        def has_laku_and_tidak_laku(combination):
            count_laku = sum(item in barang_laku for item in combination)
            count_tidak_laku = sum(item in barang_tidak_laku for item in combination)
            return count_laku > 0 and count_tidak_laku > 0

        unique_cart_product = [item for item in unique_cart_product if has_laku_and_tidak_laku(item)]
        
        # Mengubah ke DataFrame
        df_kombinasi_Produk = pd.DataFrame(unique_cart_product, columns=columns)
        df_kombinasi_Produk = df_kombinasi_Produk.reset_index(drop=True)


        def total_harga(row, price_type):
            total_price = 0
            for item in row:
                if item in listProdukTerpilih['Nama Barang'].values:
                    total_price += listProdukTerpilih[listProdukTerpilih['Nama Barang'] == item][price_type].astype(int).values[0]
            return total_price

        df_kombinasi_Produk['Total Harga Jual'] = df_kombinasi_Produk.apply(lambda row: total_harga(row, 'Harga Jual'), axis=1)
        df_kombinasi_Produk['Total Harga Beli'] = df_kombinasi_Produk.apply(lambda row: total_harga(row, 'Harga Beli'), axis=1)        
        
        def harga_bundling(row):
            num_items = len([item for item in row if pd.notna(item)])
            discount = (num_items - 3) * 6000  # Diskon sebesar 6000 per kombinasi tambahan
            return row['Total Harga Jual'] - discount
        
        df_kombinasi_Produk['Harga Bundling'] = df_kombinasi_Produk.apply(harga_bundling, axis=1)
        df_kombinasi_Produk['Keuntungan'] = df_kombinasi_Produk['Harga Bundling'] - df_kombinasi_Produk['Total Harga Beli']

        df_kombinasi_Produk = df_kombinasi_Produk.sort_values(by='Keuntungan', ascending=False,ignore_index=True).head(5)
        df_kombinasi_Produk['No'] = df_kombinasi_Produk.index + 1
        df_kombinasi_Produk['No'] = df_kombinasi_Produk['No'].astype(str)
        df_kombinasi_Produk.set_index('No', inplace=True)
        df_kombinasi_Produk['Nama Barang'] = df_kombinasi_Produk[columns].apply(lambda row: ', '.join(row.dropna()), axis=1)

        df_kombinasi_Produk_rapih = df_kombinasi_Produk[['Nama Barang','Harga Bundling','Keuntungan']]
        session_state.df_kombinasi = df_kombinasi_Produk_rapih
        return df_kombinasi_Produk
    
        
    def tampilRekomendasiBundling():
        if 'selected_rules' in session_state:    
            with st.expander('Tampilkan Kombinasi Jenis yang dipilih'):
                st.dataframe(session_state.selected_rules,use_container_width=True)
            with st.expander('Tampilkan List Produk'):
                st.markdown('<p> Tabel list produk dengan jenis yang dipilih</p>', unsafe_allow_html=True)
                st.dataframe(session_state.filter_list_produk,use_container_width=True)
            st.markdown('<h4>REKOMENDASI PAKET</h4>', unsafe_allow_html=True)
            if not session_state.df_kombinasi.empty:
                st.dataframe(session_state.df_kombinasi,use_container_width=True)
            else:
                st.warning('Tidak Ada Rekomendasi Paket yang Ditemukan, Silahkan Pilih Kombinasi Jenis Yang Lain atau membuat paket secara manual')
                if st.button('Buat Paket Bundling'):
                    session_state.selected_page = 'BuatPaketBundling'
                    st.rerun()
                
                
        else:
            st.error('Tidak Ada Rekomendasi Kombinasi Jenis, Silahkan Ganti File Transaksi dengan Periode Waktu yang berbeda')
                

    def menyimpanDataPaketBundling(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=True)
        writer.close()  # Menutup objek writer
        output.seek(0)
        data_bundling_download = output.read()
        
        st.markdown("<h4>UNDUH HASIL REKOMENDASI PAKET BUNDLING</h4>", unsafe_allow_html=True)
        st.download_button(
            label="Unduh Paket Bundling",
            data=data_bundling_download,
            file_name='rekomendasi-bundling.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key='download-button',  # Tambahkan kunci unik jika ada masalah
            use_container_width=True,
            type='primary'
        )

    def buatpaketBundling(selected_rules, list_produk):
        if 'buatpaket' not in session_state:
            session_state.buatpaket = pd.DataFrame()
        paketbundling = []
        listProduk = list_produk.copy()
        listProdukTerpilih = listProduk[listProduk['Jenis'].isin(selected_rules)]
        listProdukTerpilih['Harga Beli'] = pd.to_numeric(listProdukTerpilih['Harga Beli'], errors='coerce')
        listProdukTerpilih['Harga Jual'] = pd.to_numeric(listProdukTerpilih['Harga Jual'], errors='coerce')
        listProdukTerpilih = listProdukTerpilih.reset_index(drop=True)
        listProdukTerpilih.index = listProdukTerpilih.index + 1
        listProdukTerpilih['Pilih'] = False
        st.markdown('<h3> Pilih Produk yang ingin dibundling</h3>',unsafe_allow_html=True)
        st.markdown('<p> Pastikan memilih produk dengan jenis yang berbeda</p>',unsafe_allow_html=True)
        edited_df = st.data_editor(listProdukTerpilih, use_container_width=True, num_rows="static", disabled=['Faktur', 'Jenis', 'Nama Barang', 'Qty', 'Harga Beli', 'Harga Jual'])
        jenis_terpilih = set()
        for index, row in edited_df.iterrows():
            if row['Pilih']:
                if row['Jenis'] not in jenis_terpilih:
                    paketbundling.append(row)
                    jenis_terpilih.add(row['Jenis'])
                else:
                    st.warning(f"Produk dengan jenis '{row['Jenis']}' sudah dipilih. pilih produk dengan jenis yang berbeda.")
        session_state.buatpaket = pd.DataFrame(paketbundling)
        return pd.DataFrame(paketbundling)  # Mengembalikan DataFrame
    

    def lihatpaketBundling(produkTerpilih):
        if not produkTerpilih.empty:  # Memeriksa apakah DataFrame tidak kosong
            if 'hasilbuat' not in session_state:
                session_state.hasilbuat = pd.DataFrame()
            # Menghitung total harga jual dan harga beli
            produkTerpilih['Total Harga Jual'] = produkTerpilih['Harga Jual']
            produkTerpilih['Total Harga Beli'] = produkTerpilih['Harga Beli']
            
            # Menghitung harga bundling dengan diskon dinamis
            jumlah_produk = len(produkTerpilih)
            total_harga_jual = produkTerpilih['Total Harga Jual'].sum()
            discount = (jumlah_produk - 1) * 6000  # Diskon dinamis sesuai jumlah produk yang dipilih
            harga_bundling_total = total_harga_jual - discount
            
            # Menghitung total keuntungan
            total_harga_beli = produkTerpilih['Total Harga Beli'].sum()
            keuntungan_total = harga_bundling_total - total_harga_beli
            
            # Membuat DataFrame baru dengan semua barang dalam satu baris
            nama_barang = ', '.join(produkTerpilih['Nama Barang'])
            df_final = pd.DataFrame({
                'Nama Barang': [nama_barang],
                'Harga Bundling': [harga_bundling_total],
                'Keuntungan': [keuntungan_total]
            })
            df_final['No'] = df_final.index + 1
            df_final.set_index('No', inplace=True)
            df_final.index = df_final.index.astype(str)
            st.markdown('<h3> Paket Bundling </h3>',unsafe_allow_html=True)
            st.dataframe(df_final,use_container_width=True)
            session_state.hasilbuat = df_final
            if produkTerpilih['Jenis'].isin(session_state.selected_rules).all() and len(produkTerpilih) == len(session_state.selected_rules):
                df_download = pd.DataFrame(df_final)
                PaketBundling.menyimpanDataPaketBundling(df_download)
            # return df_final
