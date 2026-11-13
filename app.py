# PH QUEUE - V20 FINAL + Doctor License at Login
import streamlit as st
import sqlite3, math, time, datetime
import streamlit.components.v1 as components
st.set_page_config(page_title="PH QUEUE - Port Harcourt Emergency", page_icon="🚑", layout="wide")
DB = "ph_queue.db"
HOSPITALS = {
    "BMH": {"name": "BMH - Borikiri", "lat": 4.7520, "lon": 7.0230, "pass": "bmh123", "status": "Open", "beds": "Has Bed", "phone": "0803-000-0001"},
    "UPTH": {"name": "UPTH - Choba", "lat": 4.8950, "lon": 6.9200, "pass": "upth123", "status": "Open", "beds": "Has Blood", "phone": "0803-000-0002"},
    "RSUTH": {"name": "RSUTH - Okija", "lat": 4.8100, "lon": 7.0100, "pass": "rsuth123", "status": "Open", "beds": "Has ICU", "phone": "0803-000-0003"},
    "St. Michael": {"name": "St. Michael - Diobu", "lat": 4.8156, "lon": 7.0498, "pass": "stm123", "status": "Full", "beds": "No Bed", "phone": "0803-000-0004"},
    "Life Care": {"name": "Life Care - GRA", "lat": 4.7900, "lon": 7.0300, "pass": "life123", "status": "Open", "beds": "Has Bed", "phone": "0803-000-0005"},
}
DOCTORS = {
    "DR-001": {"name": "Dr. John", "hospital": "BMH", "license": "MDCN-12345", "pass": "doc123"},
    "DR-002": {"name": "Dr. Mary", "hospital": "UPTH", "license": "MDCN-67890", "pass": "doc123"},
}
DRIVERS = {"DRV-BMH-01": "BMH", "DRV-UPTH-01": "UPTH", "DRV-RSUTH-01": "RSUTH"}
def conn(): return sqlite3.connect(DB, check_same_thread=False)
def init_db():
    c = conn(); cur = c.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, password TEXT, serial TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY AUTOINCREMENT, serial TEXT, name TEXT, phone TEXT, hospital TEXT, triage TEXT, walk TEXT, bleeding TEXT, breathe TEXT, awake TEXT, address TEXT, gps TEXT, status TEXT, created TEXT, accepted INTEGER DEFAULT 0, referral TEXT DEFAULT '')")
    cur.execute("CREATE TABLE IF NOT EXISTS referrals (id INTEGER PRIMARY KEY AUTOINCREMENT, serial TEXT, from_hosp TEXT, to_hosp TEXT, reason TEXT, msg TEXT, status TEXT, created TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS counter (id INTEGER PRIMARY KEY, val INTEGER)")
    cur.execute("INSERT OR IGNORE INTO counter (id,val) VALUES (1,1000)")
    c.commit(); c.close()
init_db()
def next_serial():
    c = conn(); cur = c.cursor()
    cur.execute("UPDATE counter SET val=val+1 WHERE id=1"); c.commit()
    cur.execute("SELECT val FROM counter WHERE id=1"); v = cur.fetchone()[0]; c.close()
    return f"PHQ-{v}"
def haversine(lat1, lon1, lat2, lon2):
    R=6371; dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return round(2*R*math.asin(math.sqrt(a)),1)
def add_patient(data):
    c=conn(); cur=c.cursor()
    cur.execute("INSERT INTO patients (serial,name,phone,hospital,triage,walk,bleeding,breathe,awake,address,gps,status,created,accepted) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)", (data['serial'],data['name'],data['phone'],data['hospital'],data['triage'],data.get('walk',''),data.get('bleeding',''),data.get('breathe',''),data.get('awake',''),data.get('address',''),data.get('gps',''),'Waiting',datetime.datetime.now().strftime("%d %b %Y %I:%M %p")))
    c.commit(); c.close()
def get_patients(hosp=None):
    c=conn(); c.row_factory=sqlite3.Row; cur=c.cursor()
    if hosp: cur.execute("SELECT * FROM patients WHERE hospital=? ORDER BY id DESC",(hosp,))
    else: cur.execute("SELECT * FROM patients ORDER BY id DESC")
    rows=[dict(r) for r in cur.fetchall()]; c.close(); return rows
def accept_patient(pid):
    c=conn(); cur=c.cursor(); cur.execute("UPDATE patients SET accepted=1, status='Accepted - Ambulance Moving' WHERE id=?",(pid,)); c.commit(); c.close()
def update_status(pid,status):
    c=conn(); cur=c.cursor(); cur.execute("UPDATE patients SET status=? WHERE id=?",(status,pid)); c.commit(); c.close()
def safe_rag(serial):
    c=conn(); c.row_factory=sqlite3.Row; cur=c.cursor()
    cur.execute("SELECT * FROM patients WHERE serial=?",(serial,)); rows=[dict(r) for r in cur.fetchall()]; c.close()
    if not rows: return "No previous record found for this PHQ ID. Do not guess. Ask patient directly."
    r=rows[-1]
    return f"Retrieved from Visit on {r['created']}, {r['hospital']}. Name: {r['name']}, Phone: {r['phone']}, Last Triage: {r['triage']}, Bleeding: {r['bleeding']}, Address: {r['address']}. Source: ph_queue.db - patients table. No data invented."
def play_beep_if_needed(has_pending, sound_enabled):
    if has_pending and sound_enabled:
        components.html("""<script>function beep(){ try{ const ctx=new (window.AudioContext||window.webkitAudioContext)(); const o=ctx.createOscillator(); const g=ctx.createGain(); o.connect(g); g.connect(ctx.destination); o.frequency.value=880; o.type='sine'; g.gain.value=0.2; o.start(); o.stop(ctx.currentTime+0.3); setTimeout(()=>{ const o2=ctx.createOscillator(); const g2=ctx.createGain(); o2.connect(g2); g2.connect(ctx.destination); o2.frequency.value=880; o2.type='sine'; g2.gain.value=0.2; o2.start(); o2.stop(ctx.currentTime+0.3); },400); }catch(e){} } beep(); setInterval(beep,3000);</script>""", height=0)
for k in ["role","user","hospital","serial","chosen_hosp","step","triage_data","sound_on","muted_until"]:
    if k not in st.session_state: st.session_state[k]=None if k!="sound_on" else False
if st.session_state["triage_data"] is None: st.session_state["triage_data"]={}
if st.session_state["muted_until"] is None: st.session_state["muted_until"]=0
st.title("🚑 PH QUEUE - Port Harcourt Smart Emergency")
st.caption("Find Nearby Hospital FIRST → AI Triage → Ambulance with GPS → Doctor Referral")
if not st.session_state["role"]:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Victim","🏥 Hospital","🚑 Driver","👨‍⚕️ Doctor","🛡️ Admin"])
    with tab1:
        st.subheader("Victim Login / Register")
        name=st.text_input("Full Name", key="vname"); phone=st.text_input("Phone", key="vphone"); pw=st.text_input("Password", type="password", key="vpw")
        if st.button("Login / Register as Victim"):
            c=conn(); cur=c.cursor(); cur.execute("SELECT * FROM users WHERE phone=?",(phone,)); row=cur.fetchone()
            if row:
                if row[2]!=pw: st.error("Wrong password"); st.stop()
                serial=row[3]
            else:
                serial=next_serial(); cur.execute("INSERT INTO users VALUES (?,?,?,?)",(phone,name,pw,serial)); c.commit()
            c.close(); st.session_state.update(role="victim", user=name or "Victim", hospital=None, serial=serial); st.rerun()
    with tab2:
        hosp=st.selectbox("Hospital", list(HOSPITALS.keys())); hpw=st.text_input("Hospital Password", type="password", key="hpw")
        if st.button("Login as Hospital"):
            if hpw==HOSPITALS[hosp]["pass"]: st.session_state.update(role="hospital", hospital=hosp); st.rerun()
            else: st.error("Wrong hospital password")
    with tab3:
        dcode=st.text_input("Driver Code e.g DRV-BMH-01"); dhosp=st.selectbox("Your Hospital", list(HOSPITALS.keys()), key="dhosp")
        if st.button("Login as Driver"):
            if dcode in DRIVERS and DRIVERS[dcode]==dhosp: st.session_state.update(role="driver", hospital=dhosp, user=dcode); st.rerun()
            else: st.error("Wrong driver code / hospital")
    with tab4:
        st.subheader("Doctor Login - License Required")
        st.caption("Only Admin can create Doctor. Must have MDCN License. No license = No account. Doctor must enter ID + License + Password every login.")
        did=st.text_input("Doctor ID e.g DR-001")
        dlic=st.text_input("Medical License Number e.g MDCN-12345 - Required")
        dpw=st.text_input("Doctor Password", type="password", key="dpw")
        if st.button("Login as Doctor"):
            if did in DOCTORS and DOCTORS[did]["license"].strip().upper()==dlic.strip().upper() and DOCTORS[did]["pass"]==dpw:
                st.session_state.update(role="doctor", user=DOCTORS[did]["name"], hospital=DOCTORS[did]["hospital"]); st.rerun()
            elif did in DOCTORS and DOCTORS[did]["license"].strip().upper()!=dlic.strip().upper():
                st.error("❌ License does not match this Doctor ID. Access Denied. Contact Admin.")
            else: st.error("Wrong Doctor ID / License / Password or No License. Only licensed doctors can login.")
    with tab5:
        apw=st.text_input("Admin Password", type="password", key="apw")
        if st.button("Login as Admin"):
            if apw=="admin123": st.session_state.update(role="admin"); st.rerun()
            else: st.error("Wrong admin password")
    st.stop()
if st.button("Logout"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
if st.session_state["role"]=="victim":
    st.success(f"Welcome {st.session_state['user']} | Your ID: **{st.session_state['serial']}** | Keep this ID for hospital to retrieve your record")
    if not st.session_state["chosen_hosp"]:
        st.subheader("Step 2 - 📍 Find Nearby Hospital For Me (BEFORE AI Questions)")
        st.info("We find the closest OPEN hospital first, then AI triage starts for THAT hospital.")
        col1,col2=st.columns(2)
        with col1: my_lat=st.number_input("Your GPS Latitude", value=4.8156, format="%.4f")
        with col2: my_lon=st.number_input("Your GPS Longitude", value=7.0498, format="%.4f")
        area=st.text_input("If GPS blocked, type your area: Diobu / Mile 1 / Choba / Borikiri / GRA", placeholder="e.g Diobu, Mile 1")
        if st.button("📍 Share My GPS - Click Allow / Accept"):
            st.success(f"GPS Saved: {my_lat}, {my_lon}"); st.session_state["gps"]=f"{my_lat},{my_lon}"
        ranked=[]
        for code, h in HOSPITALS.items():
            d=haversine(my_lat, my_lon, h["lat"], h["lon"]); ranked.append((d, code, h))
        ranked.sort()
        st.write("### Nearby Hospitals - Closest First")
        for d, code, h in ranked:
            status_icon="🟢" if h["status"]=="Open" else "🔴"; mins=int(d*3.5)
            c1,c2,c3=st.columns([3,1,1])
            with c1: st.write(f"**{h['name']}** - {d} km - ~{mins} mins - {status_icon} {h['status']} - {h['beds']} - 📞 {h['phone']}")
            with c2:
                if h["status"]=="Full": st.warning("Full - Try next open")
                elif st.button(f"Choose {code}", key=f"ch_{code}"):
                    st.session_state["chosen_hosp"]=code; st.session_state["step"]="triage"; st.rerun()
        st.caption("If GPS blocked, we use your typed area to suggest. If no internet, call hospital number above.")
        st.stop()
    hosp = st.session_state["chosen_hosp"]
    st.info(f"Chosen Hospital: **{HOSPITALS[hosp]['name']}**")
    if st.button("Change Hospital"): st.session_state["chosen_hosp"]=None; st.rerun()
    td=st.session_state["triage_data"]
    st.subheader(f"Step 3 - AI Nurse Triage for {hosp} - Rule-Based, No Hallucination")
    if "walk" not in td:
        td["walk"]=st.radio("Q1: Can you walk?", ["Yes","No"], key="q1")
        if st.button("Next"): st.session_state["triage_data"]=td; st.rerun()
    elif "bleeding" not in td:
        td["bleeding"]=st.radio("Q2: Are you bleeding?", ["No","Small","Heavy"], key="q2")
        if st.button("Next"):
            if td["walk"]=="No" and td["bleeding"]=="Heavy": st.session_state["fast_jump"]=True; st.warning("⚠️ CRITICAL! Ambulance NOW. Drop address + phone quickly!")
            st.session_state["triage_data"]=td; st.rerun()
    elif st.session_state.get("fast_jump") and "address" not in td:
        st.error("🚨 FAST JUMP ACTIVE - Ambulance Starting Now")
        td["address"]=st.text_input("Drop address + phone together (e.g Diobu, Mile 1 near Market - 0803-123-4567)")
        if st.button("Send Address + Phone - Start Ambulance"):
            td["triage"]="CRITICAL"; td["gps"]=st.session_state.get("gps","4.8156,7.0498")
            add_patient({"serial":st.session_state["serial"],"name":st.session_state["user"],"phone":td["address"],"hospital":hosp,"triage":"CRITICAL","walk":td["walk"],"bleeding":td["bleeding"],"breathe":"Pending","awake":"Pending","address":td["address"],"gps":td["gps"]})
            st.session_state["triage_data"]=td; st.session_state["step"]="done_fast"; st.rerun()
    elif "breathe" not in td:
        td["breathe"]=st.radio("Q3: Can you breathe?", ["Yes","No"], key="q3")
        if st.button("Next"): st.session_state["triage_data"]=td; st.rerun()
    elif "awake" not in td:
        td["awake"]=st.radio("Q4: Are you awake?", ["Yes","No"], key="q4")
        if st.button("Next"): st.session_state["triage_data"]=td; st.rerun()
    elif "address" not in td:
        if td["bleeding"]=="Heavy" or td["breathe"]=="No" or td["walk"]=="No": tri="CRITICAL"
        elif td["bleeding"]=="Small": tri="SERIOUS"
        else: tri="GENERAL"
        st.info(f"AI Decision: **{tri}**")
        if tri=="CRITICAL": st.error("Ambulance Needed. Drop address + phone + GPS.")
        td["address"]=st.text_input("Drop address + phone together (e.g Diobu, Mile 1 - 0803-123-4567)")
        if tri=="CRITICAL":
            if st.button("📍 Share My GPS"):
                st.session_state["gps"]=f"{st.session_state.get('gps','4.8156,7.0498')}"; st.success("GPS Saved - Ambulance will use GPS + Address + Phone")
        if st.button("Submit - Book Ticket / Send Ambulance"):
            td["triage"]=tri; td["gps"]=st.session_state.get("gps","")
            add_patient({"serial":st.session_state["serial"],"name":st.session_state["user"],"phone":td["address"],"hospital":hosp,"triage":tri,"walk":td["walk"],"bleeding":td["bleeding"],"breathe":td["breathe"],"awake":td["awake"],"address":td["address"],"gps":td["gps"]})
            st.session_state["triage_data"]=td; st.session_state["step"]="done"; st.rerun()
    else:
        st.success(f"Done! Your case for {hosp} is booked. Triage: {td.get('triage')}. Your ID: {st.session_state['serial']}")
        if st.button("Start New Case"): st.session_state["triage_data"]={}; st.session_state["chosen_hosp"]=None; st.session_state["fast_jump"]=False; st.rerun()
    st.stop()
if st.session_state["role"] in ["hospital","driver","doctor","admin"]:
    hosp = st.session_state.get("hospital") if st.session_state["role"]!="admin" else None
    pats = get_patients(hosp) if hosp else get_patients(None)
    pending = [p for p in pats if p['triage']=="CRITICAL" and p['accepted']==0]
    st.subheader(f"General Dashboard - {hosp or 'ALL HOSPITALS (Admin)'}")
    if st.session_state["role"] in ["hospital","driver"]:
        if not st.session_state["sound_on"]:
            if st.button("🔊 Click Here To Enable Emergency Sound"): st.session_state["sound_on"]=True; st.rerun()
        else: st.success("🔊 Emergency Sound Enabled - Will beep ONLY when ambulance needed")
        if st.button("🔇 Mute Sound For 1 Minute"): st.session_state["muted_until"]=time.time()+60; st.success("Muted for 1 min.")
    is_muted = time.time() < st.session_state["muted_until"]
    has_pending = len(pending)>0 and not is_muted
    play_beep_if_needed(has_pending, st.session_state["sound_on"])
    st.write("### 🔍 Search Patient By PHQ ID / Phone / Name - Safe RAG (Records Only)")
    q=st.text_input("Enter PHQ-XXXX or Phone")
    if q:
        st.info(safe_rag(q) if q.startswith("PHQ") else f"Search for {q} - Use PHQ ID for exact RAG record.")
        for p in pats:
            if q in p['serial'] or q in p['phone'] or q.lower() in p['name'].lower(): st.write(f"Found: {p['serial']} - {p['name']} - {p['hospital']} - {p['triage']} - {p['status']}")
    st.write("### 🚨 EMERGENCY - PINNED AT TOP UNTIL ACCEPT - CANNOT BE HIDDEN")
    if pending:
        for p in pending:
            st.error(f"🚨 {p['serial']} - {p['name']} - {p['hospital']} - {p['triage']} - Bleeding: {p['bleeding']} - Walk: {p['walk']} - Time: {p['created']} - WAITING - NOT YET ACCEPTED")
            st.write(f"**📍 GPS (Top):** https://www.google.com/maps?q={p['gps']}")
            st.write(f"**📍 Address (Middle):** {p['address']}")
            st.write(f"**📞 Phone (Bottom):** {p['phone']} [ 📞 CALL VICTIM NOW ]")
            c1,c2,c3=st.columns(3)
            with c1:
                if st.button(f"🚑 ACCEPT & SEND AMBULANCE - {p['serial']}", key=f"acc_{p['id']}"): accept_patient(p['id']); st.success("Accepted! Sound stopped. Ambulance moving."); st.rerun()
            with c2:
                if st.button(f"📞 Call Victim {p['serial']}", key=f"call_{p['id']}"): st.info(f"Calling {p['phone']}")
            with c3:
                if st.button(f"✅ Picked Up {p['serial']}", key=f"pick_{p['id']}"): update_status(p['id'],"Picked Up"); st.rerun()
    else: st.success("No pending ambulance emergency. All accepted or no critical case.")
    st.write("### All Patients - Accepted Moves Down Here, Still Tracked")
    for p in pats:
        st.write(f"{p['serial']} - {p['name']} - {p['hospital']} - {p['triage']} - Status: {p['status']} - Accepted: {'Yes' if p['accepted'] else 'No'}")
        if st.session_state["role"] in ["hospital","admin"]:
            if st.button(f"Mark Treated {p['serial']}", key=f"tr_{p['id']}"): update_status(p['id'],"Treated"); st.rerun()
    if st.session_state["role"]=="doctor":
        st.write("---")
        st.write("### 👨‍⚕️ Doctor-Only Referral + Consultation Chat - Verified Doctors Only")
        st.caption("Victim CANNOT see this. Only doctors with MDCN License.")
        serial_ref=st.text_input("Patient PHQ ID to Refer")
        to_hosp=st.selectbox("Refer To Hospital", list(HOSPITALS.keys()))
        reason=st.selectbox("Why Refer?", ["No bed","No blood","Need specialist","Need ICU","Need surgery"])
        msg=st.text_area("Message to Other Doctor")
        if st.button("🔁 Send Referral"):
            c=conn(); cur=c.cursor(); cur.execute("INSERT INTO referrals (serial,from_hosp,to_hosp,reason,msg,status,created) VALUES (?,?,?,?,?,?,?)",(serial_ref,hosp,to_hosp,reason,msg,"Pending",datetime.datetime.now().strftime("%d %b %Y %I:%M %p"))); c.commit(); c.close(); st.success(f"Referral sent {hosp} -> {to_hosp} for {serial_ref}")
        c=conn(); c.row_factory=sqlite3.Row; cur=c.cursor(); cur.execute("SELECT * FROM referrals ORDER BY id DESC"); refs=[dict(r) for r in cur.fetchall()]; c.close()
        for r in refs:
            st.write(f"Referral: {r['serial']} {r['from_hosp']} -> {r['to_hosp']} | {r['reason']} | {r['msg']} | Status: {r['status']}")
            cc1,cc2,cc3=st.columns(3)
            with cc1:
                if st.button(f"✅ Accept Referral {r['id']}", key=f"ra_{r['id']}"): c=conn(); cur=c.cursor(); cur.execute("UPDATE referrals SET status='Accepted' WHERE id=?",(r['id'],)); c.commit(); c.close(); st.rerun()
            with cc2:
                if st.button(f"❌ Decline {r['id']}", key=f"rd_{r['id']}"): c=conn(); cur=c.cursor(); cur.execute("UPDATE referrals SET status='Declined - Try Another' WHERE id=?",(r['id'],)); c.commit(); c.close(); st.rerun()
            with cc3:
                if st.button(f"💬 Share Record {r['serial']}", key=f"rs_{r['id']}"): st.info(safe_rag(r['serial']))
        st.info("Victim sees only: 'Your doctor is referring you to UPTH, please wait, ambulance is coming' - No medical details shown to victim.")
    if st.session_state["role"]=="admin":
        st.write("---"); st.write("### Admin - Create Doctor (Must Have License)")
        st.write("Doctor creation requires Full Name + Hospital + MDCN License. No license = No account. (Demo: DR-001 / MDCN-12345 / doc123, DR-002 / MDCN-67890 / doc123)")
