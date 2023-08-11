import os
from flask import Flask, redirect, render_template, request, url_for, session, flash
import psycopg2
from psycopg2 import pool

# Yukarıda gerekli kütüphaneleri importladık

#  Aşağıdaki iki satır Önemsiz 
app = Flask(__name__)
app.secret_key = 'your secret key2' 

# DATABASE CONNECTION YAPTIĞIMIZ YER
# BAĞLANABİLMENİZ İÇİN İP ADRESLERİNİZİ BARBAROS BEY'E İLETMENİZ GEREKİYOR. İNTERNETE "What is my external IP" yazarak ulaşabilirsiniz
minconn = 3
maxconn = 10
conn_pool = psycopg2.pool.SimpleConnectionPool(minconn, maxconn, 
                                                user = "postgres",
                                                password = "postgres",
                                                host = "20.203.212.232",
                                                port = "5435",
                                                database = "internprj")

# LOGIN SAYFASININ FONKSİYONLARI
# ALTTAKİ POST FONKSİYONU KULLANICIDAN ID ALIP DATABASE'E QUERY ATIYOR VE O ID İLE EŞLEŞEN MÜHENDİS İLE OTURUM AÇIYOR VE ARDINDAN DASHBOARD SAYFASINA YÖNLENDİRİYOR
@app.route('/', methods=['GET', 'POST'])
def index():

    conn = conn_pool.getconn() # database bağlantısı sağla
    cur = conn.cursor() # query atmaya hazırlan
    cur.execute('SELECT * FROM engineer')
    engineers_li = cur.fetchall()

    if request.method == 'POST':

        #changed this do I need to change it back to engineer_id
        engineer_id= request.form.get('engineerID') # login.html kısmından engineerID çekildi (kullanıcıdan)
        #parametre haline getiriyor

        conn = conn_pool.getconn() # database bağlantısı sağlandı
        try:
            cur = conn.cursor() # database'e query gönderilmeye hazırlandı
            cur.execute('SELECT * FROM engineer WHERE engineer_id = %s', (engineer_id,)) # engineer idsi kullanıcıdan alınan id'ye eşit olan engineer databaseden istendi
            #words like where go with the select * from to get certain things
            # %s shows that you are going to give the user inputted value
            result = cur.fetchone() # database'in döndüğü sonuç (cur.fetchone = ilk satırdaki sonuç, cut.fetchall = tüm sonuçlar. Bize sadece ilk satırdaki sonuç lazım (bir id ile sadece tek bir mühendis olabilir))
            if result:
                session['engineer'] = result # elde ettiğimiz engineer ile oturum açtık. Bundan sonra kullanıcı ismine ya da idsine ihtiyacımız olduğu zaman session.get('engineer') ile elde edeceğiz
                return redirect(url_for('dashboard')) # dashboard.html yükledik (renderladık)
            
            else:
                return redirect(url_for('index')) # eğer database hiçbir bilgi dönmezse login sayfasını tekrar yüklüyor
        finally:
            conn_pool.putconn(conn) # en son database bağlantısını kes (database ile şimdilik işimiz bitti)
    return render_template('login.html', list_engineers=engineers_li)


@app.route('/save', methods=['POST'])
def save():
    conn = conn_pool.getconn() # database bağlantısı sağlandı
    cur = conn.cursor() # database'e query gönderilmeye hazırlandı
    
    if request.method == 'POST':
        engineer_id_new = request.form.get('engineerNewID') # login.html kısmından engineerID çekildi (kullanıcıdan)
        engineer_name_new = request.form.get('engineerNameNew') # login.html kısmından engineerID çekildi (kullanıcıdan)
        cur.execute("INSERT INTO public.engineer(engineer_id, engineer_name) VALUES (DEFAULT, %s)", (engineer_name_new,))
        #inserts engineer with given values taken from params engineer_name_new ...
        conn.commit()
        flash('Basariyla eklendi')
    return redirect(url_for('index'))


@app.route('/engineers', methods=['GET'])
def engineers():

    conn = conn_pool.getconn() # database bağlantısı sağla
    cur = conn.cursor() # query atmaya hazırlan
    cur.execute('SELECT * FROM engineer') # tüm MIP'leri almak için query yaz
    engineers_li = cur.fetchall() # databasein döndüğü tüm sonuçları al ve mips isimli variableın içine kaydet
    conn_pool.putconn(conn) # database bağlantısını kes
    return render_template('dashboard.html', list_engineer=engineers_li)



# DASHBOARD SAYFASI İÇİN ÇAĞIRACAĞIMIZ FONKSİYONLAR
# AŞAĞIDAKİ FONKSİYON DATABASEDE MEVCUT OLAN TÜM MIP'LERİ ALIP O LİSTE İLE dashboard.html İSİMLİ SAYFAYI YÜKLÜYOR.
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    engineer = session.get('engineer') # açtığımız oturumdan engineer (mevcut kullanıcı) bilgilerini çekebiliriz. Oturum açtığımız için sürekli database'e query atmamıza gerek yok.
    
    #how do i get the id of the engineer that has been grabbed?
    this_engineer_id = session.get('engineer_id')
   
    if engineer is None: # mevcutta bir oturum açık değilse login sayfasına geri dön
        return redirect(url_for('index')) 

    conn = conn_pool.getconn() # database bağlantısı sağla

    try:
        cur = conn.cursor() # query atmaya hazırlan
        cur.execute('SELECT * FROM mip') # tüm MIP'leri almak için query yaz
        mips = cur.fetchall()
        cur.execute("""
        SELECT E.ENGINEER_NAME, LP.NAME, LPS.LP_STEP_NAME,T.ISCOMPLETE FROM ENGLPSTEPCOMPLETION T
        LEFT JOIN ENGINEER E ON E.ENGINEER_ID = T.ENGINEER_ID
        LEFT JOIN LEARNINGPATHSTEPS LPS ON LPS.LP_STEP_ID = T.LP_STEP_ID
        LEFT JOIN LEARNINGPATH LP ON LP.LEARNINGPATH_ID = LPS.LP_ID
        WHERE E.ENGINEER_ID=%s
        ORDER BY 2 ASC
        """, (engineer[0],) )
        par = cur.fetchall()

        cur.execute("""
        WITH KOD AS (
        SELECT E.ENGINEER_NAME AS NAME,
        LP.NAME AS LPNAME,
        LPS.LP_STEP_NAME AS LPSNAME,
        T.ISCOMPLETE AS RESULT
        FROM ENGLPSTEPCOMPLETION T
        LEFT JOIN ENGINEER E ON E.ENGINEER_ID = T.ENGINEER_ID
        LEFT JOIN LEARNINGPATHSTEPS LPS ON LPS.LP_STEP_ID = T.LP_STEP_ID
        LEFT JOIN LEARNINGPATH LP ON LP.LEARNINGPATH_ID = LPS.LP_ID
        WHERE E.ENGINEER_ID = %s
        ORDER BY 2 ASC
        )
        SELECT KOD.LPNAME,
        COUNT(CASE WHEN KOD.RESULT = 'False' THEN 1 END) AS FalseR,
        COUNT(CASE WHEN KOD.RESULT = 'True' THEN 1 END) AS TrueR,
        CASE WHEN COUNT(CASE WHEN KOD.RESULT = 'False' THEN 1 END) = 0 THEN 'LP bitmiştir'
        ELSE 'LP bitmemiştir'
        END AS LP_STATUS
        FROM KOD
        GROUP BY KOD.LPNAME
        ORDER BY KOD.LPNAME;
        """, (engineer[0],))
        parComplete = cur.fetchall()

    finally:
        conn_pool.putconn(conn) # database bağlantısını kes

    return render_template('dashboard.html', engineer=engineer, mips=mips, list_par=par, list_complete=parComplete) # dashboard.htmli yükle ve ona engineer(mevcut oturum) ve databaseden elde ettiğimiz mips listesini yükle.

# FONKSİYON PROTOTİPİ (İÇİNİ DOLDURUN)
@app.route('/paths/<mip_id>', methods=['GET'])
def paths(mip_id):
    
    conn = conn_pool.getconn()
    cur = conn.cursor() 
    cur.execute('SELECT * FROM learningpath WHERE mip_id = %s', (mip_id,)) 
    result = cur.fetchall() 
    print(result)
    conn_pool.putconn(conn) 
    return render_template('paths.html', list_mips=result)


@app.route('/pathsteps/<learningpath_id>', methods=['GET'])
def pathsteps(learningpath_id):
    
    conn = conn_pool.getconn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM learningpathsteps WHERE lp_id = %s', (learningpath_id,)) 
    result = cur.fetchall() 
    print(result)
    conn_pool.putconn(conn) 
    return render_template('pathsteps.html', list_steps=result)


'''
@app.route('/update', methods=['GET', 'POST'])
def update():

    engineer_taken = session.get('engineer')

    if engineer_taken is None: 
        return redirect(url_for('index')) 
    
    engineer_id_update = request.form.get('engineerUpdateID')
    engineer_name_update = request.form.get('engineerNameUpdate')

    conn = conn_pool.getconn() # database bağlantısı sağla
    cur = conn.cursor()
    cur.execute('UPDATE engineer SET engineer_id = DEFAULT, engineer_name = %s', (engineer_name_update))
    conn_pool.putconn(conn) # database bağlantısını kes

    return render_template('update.html', engineer=engineer_taken)
'''

@app.route('/update/<engineer_id>', methods=['POST'])
def update_engineer(engineer_id):
    if request.method == 'POST':
        engineer_name = request.form['engineer_name']
         
        conn = conn_pool.getconn() 
        cur = conn.cursor()
        cur.execute("""
            UPDATE engineer
            SET engineer_name = %s
            WHERE engineer_id = %s
            """, (engineer_name, engineer_id))

        flash('Student Updated Successfully')
        conn.commit()
        return redirect(url_for('index'))

@app.route('/edit/<engineer_id>', methods = ['POST', 'GET'])
def edit(engineer_id):

    conn = conn_pool.getconn() 
    cur = conn.cursor()
    cur.execute('SELECT * FROM engineer WHERE engineer_id = {0}'.format(engineer_id))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit.html', engineer = data[0])

@app.route('/edit_mip/<mip_id>', methods = ['POST', 'GET'])
def edit_mip(mip_id):

    conn = conn_pool.getconn() 
    cur = conn.cursor()
    cur.execute('SELECT * FROM mip WHERE mip_id = {0}'.format(mip_id))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('editMIP.html', mip = data[0])

@app.route('/update_mip/<mip_id>', methods=['POST'])
def update_mip(mip_id):
    if request.method == 'POST':
        mip_name = request.form['mip_name']
         
        conn = conn_pool.getconn() 
        cur = conn.cursor()
        cur.execute("""
            UPDATE mip
            SET mip_name = %s
            WHERE mip_id = %s
            """, (mip_name, mip_id))

        flash('Student Updated Successfully')
        conn.commit()
        return redirect(url_for('dashboard'))

@app.route('/save_mip', methods=['POST'])
def save_mip():
    conn = conn_pool.getconn() # database bağlantısı sağlandı
    cur = conn.cursor() # database'e query gönderilmeye hazırlandı
    
    if request.method == 'POST':
        engineer_mip_new = request.form.get('mipNameNew') # login.html kısmından engineerID çekildi (kullanıcıdan)
        cur.execute("INSERT INTO public.mip(mip_id, mip_name) VALUES (DEFAULT, %s)", (engineer_mip_new,))
        #inserts engineer with given values taken from params engineer_name_new ...
        conn.commit()
        flash('Basariyla eklendi')
    return redirect(url_for('dashboard'))


@app.route('/delete/<engineer_id>', methods = ['POST','GET'])
def delete(engineer_id):

    conn = conn_pool.getconn() 
    cur = conn.cursor()
    cur.execute('DELETE FROM engineer WHERE engineer_id = {0}'.format(engineer_id))
    conn.commit()
    #flash('Student Removed Successfully')

    #return render_template('login.html')
    return redirect(url_for('index'))

@app.route('/delete_mip/<mip_id>', methods = ['POST','GET'])
def delete_mip(mip_id):

    conn = conn_pool.getconn() 
    cur = conn.cursor()
    cur.execute('DELETE FROM mip WHERE mip_id = {0}'.format(mip_id))
    conn.commit()

    return redirect(url_for('dashboard'))

# MAIN FONKSİYONUMUZ (ÖNEMSİZ) OLDUĞU GİBİ BIRAKABİLİRSİNİZ
if __name__ == '__main__':
    app.run()