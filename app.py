# PH QUEUE - V26 FULL - Hospital Departments + Referral + Chat
# Victim -> Receptionist -> General Doctor (Consultation Boss) -> Lab / Radiographer / Dentist / Pharmacy -> Back to General Doctor -> Treated / Transfer
import streamlit as st
import sqlite3, math, time, datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="PH QUEUE V26 - Port Harcourt Emergency", page_icon="🚑", layout="wide")
DB = "ph_queue_v26.db"

HOSPITALS = {
    "BMH": {"name": "BMH - Borikiri", "lat": 4.7520, "lon": 7.0230, "phone": "0803-000-0001"},
    "UPTH": {"name": "UPTH - Choba", "lat": 4.8950, "lon": 6.9200, "phone": "0803-000-0002"},
    "RSUTH": {"name": "RSUTH - Okija", "lat": 4.8100, "lon": 7.0100, "phone": "0803-000-0003"},
    "St. Michael": {"name": "St. Michael - Diobu", "lat": 4.8156, "lon": 7.0498, "phone": "0803-000-0004"},
    "Life Care": {"name": "Life Care - GRA", "lat": 4.7900, "lon": 7.0300, "phone": "0803-000-0005"},
}

# STAFF - Each hospital has its own staff. Admin creates these in real life.
# Format: ID : {name, hospital, role, license (for doctors), pass}
# Roles: admin, receptionist, general_doctor, dentist, lab, radiographer, pharmacist, driver
STAFF = {
    # RSUTH
    "RSUTH-ADMIN": {"name": "RSUTH Admin", "hospital": "RSUTH", "role": "admin", "pass": "admin123"},
    "RSUTH-REC01": {"name": "Ada Receptionist", "hospital": "RSUTH", "role": "receptionist", "pass": "recep123"},
    "RSUTH-GD01": {"name": "Dr. John - General", "hospital": "RSUTH", "role": "general_doctor", "license": "MDCN-12345", "pass": "doc123"},
    "RSUTH-DEN01": {"name": "Dr. Smile - Dentist", "hospital": "RSUTH", "role": "dentist", "license": "MDCN-22222", "pass": "doc123"},
    "RSUTH-LAB01": {"name": "Lab Tech Chidi", "hospital": "RSUTH", "role": "lab", "pass": "lab123"},
    "RSUTH-RAD01": {"name": "Radiographer Ngozi", "hospital": "RSUTH", "role": "radiographer", "pass": "rad123"},
    "RSUTH-PHA01": {"name": "Pharmacist Emeka", "hospital": "RSUTH", "role": "pharmacist", "pass": "pha123"},
    # UPTH
    "UPTH-ADMIN": {"name": "UPTH Admin", "hospital": "UPTH", "role": "admin", "pass": "admin123"},
    "UPTH-REC01": {"name": "UPTH Receptionist", "hospital": "UPTH", "role": "receptionist", "pass": "recep123"},
    "UPTH-GD01": {"name": "Dr. Mary - General", "hospital": "UPTH", "role": "general_doctor", "license": "MDCN-67890", "pass": "doc123"},
    "UPTH-DEN01": {"name": "Dr. Teeth - Dentist", "hospital": "UPTH", "role": "dentist", "license": "MDCN-33333", "pass": "doc123"},
    "UPTH-LAB01": {"name": "UPTH Lab", "hospital": "UPTH", "role": "lab", "pass": "lab123"},
    "UPTH-RAD01": {"name": "UPTH Radiographer", "hospital": "UPTH", "role": "radiographer", "pass": "rad123"},
    "UPTH-PHA01": {"name": "UPTH Pharmacist", "hospital": "UPTH", "role": "pharmacist", "pass": "pha123"},
    # BMH
    "BMH-ADMIN": {"name": "BMH Admin", "hospital": "BMH", "role": "admin", "pass": "admin123"},
    "BMH-REC01": {"name": "BMH Receptionist", "hospital": "BMH", "role": "receptionist", "pass": "recep123"},
    "BMH-GD01": {"name": "Dr. BMH General", "hospital": "BMH", "role": "general_doctor", "license": "MDCN-11111", "pass": "doc123"},
    "BMH-LAB01": {"name": "BMH Lab", "hospital": "BMH", "role": "lab", "pass": "lab123"},
    "BMH-RAD01": {"name": "BMH Radiographer", "hospital": "BMH", "role": "radiographer", "pass": "rad123"},
    "BMH-PHA01": {"name": "BMH Pharmacist", "hospital": "BMH", "role": "pharmacist", "pass": "pha123"},
    "BMH-DEN01": {"name": "BMH Dentist", "hospital": "BMH", "role": "dentist", "license": "MDCN-44444", "pass": "doc123"},
}

DRIVERS = {"DRV-BMH-01": "BMH", "DRV-UPTH-01": "UPTH", "DRV-RSUTH-01": "RSUTH"}
ROLE_LABEL = {"admin": "👑 Admin", "receptionist": "🧑‍💼 Receptionist", "general_doctor": "🩺 General Doctor", "dentist": "🦷 Dentist", "lab": "🔬 Lab", "radiographer": "🩻 Radiographer", "pharmacist": "💊 Pharmacist", "driver": "🚑 Driver"}

def conn(): return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    c = conn(); cur = c.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, password TEXT, serial TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY AUTOINCREMENT, serial TEXT, name TEXT, phone TEXT, hospital TEXT, triage TEXT, walk TEXT, bleeding TEXT, breathe TEXT, awake TEXT, address TEXT, gps TEXT, status TEXT, created TEXT, accepted INTEGER DEFAULT 0, assigned_to TEXT DEFAULT '', referral TEXT DEFAULT '')")
    # Internal referral: General Doctor -> Dept inside same hospital
    cur.execute("CREATE TABLE IF NOT EXISTS internal_referrals (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_serial TEXT, patient_name TEXT, hospital TEXT, from_doctor TEXT, to_dept TEXT, test_type TEXT, note TEXT, status TEXT, created TEXT, result TEXT DEFAULT '')")
    # External referral: Hospital -> Hospital
    cur.execute("CREATE TABLE IF NOT EXISTS referrals (id INTEGER PRIMARY KEY AUTOINCREMENT, serial TEXT, from_hosp TEXT, to_hosp TEXT, reason TEXT, msg TEXT, status TEXT, created TEXT)")
    # Chat between hospitals / doctors
    cur.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, from_hosp TEXT, from_name TEXT, to_hosp TEXT, msg TEXT, created TEXT)")
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
def assign_patient(pid, doctor_name):
    c=conn(); cur=c.cursor(); cur.execute("UPDATE patients SET assigned_to=?, status=? WHERE id=?",(doctor_name, f"Assigned to {doctor_name}", pid)); c.commit(); c.close()

def safe_rag(serial):
    c=conn(); c.row_factory=sqlite3.Row; cur=c.cursor()
    cur.execute("SELECT * FROM patients WHERE serial=?",(serial,)); rows=[dict(r) for r in cur.fetchall()]; c.close()
    if not rows: return "No previous record found for this PHQ ID. Do not guess. Ask patient directly."
    r=rows[-1]
    return f"Retrieved from Visit on {r['created']}, {r['hospital']}. Name: {r['name']}, Phone: {r['phone']}, Last Triage: {r['triage']}, Bleeding: {r['bleeding']}, Address: {r['address']}. Source: ph_queue.db - patients table. No data invented."

def play_beep_if_needed(has_pending, sound_enabled):
    if has_pending and sound_enabled:
        components.html("""<script>function beep(){ try{ const ctx=new (window.AudioContext||window.webkitAudioContext)(); const o=ctx.createOscillator(); const g=ctx.createGain(); o.connect(g); g.connect(ctx.destination); o.frequency.value=880; o.type='sine'; g.gain.value=0.2; o.start(); o.stop(ctx.currentTime+0.3); setTimeout(()=>{ const o2=ctx.createOscillator(); const g2=ctx.createGain(); o2.connect(g2); g2.connect(ctx.destination); o2.frequency.value=880; o2.type='sine'; g2.gain.value=0.2; o2.start(); o2.stop(ctx.currentTime+0.3); },400); }catch(e){} } beep(); setInterval(beep,3000);</script>""", height=0)

# Session defaults
for k in ["role","user","hospital","serial","chosen_hosp","step","triage_data","sound_on","muted_until","staff_id"]:
    if k not in st.session_state: st.session_state[k]=None if k!="sound_on" else False
if st.session_state["triage_data"] is None: st.session_state["triage_data"]={}
if st.session_state["muted_until"] is None: st.session_state["muted_until"]=0

st.title("🚑 PH QUEUE V26 - Port Harcourt Smart Emergency")
st.caption("Victim → Receptionist → General Doctor (Consultation Boss) → Lab / Radiographer / Dentist / Pharmacy → Treated / Transfer")

# ============ LOGIN ============
if not st.session_state["role"]:
    tab1, tab2, tab3 = st.tabs(["👤 Victim","🏥 Hospital Staff - All Departments","🚑 Driver"])
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
        st.subheader("Hospital Staff Login - One Hospital, Many Departments")
        st.caption("Choose Hospital → Choose Your Department → Enter Staff ID + Password. Each department sees only its own work.")
        hosp=st.selectbox("Choose Hospital", list(HOSPITALS.keys()), key="staff_hosp")
        # Show available roles for that hospital
        roles_for_hosp = sorted(set([v["role"] for v in STAFF.values() if v["hospital"]==hosp]))
        role_choice = st.selectbox("Choose Your Department / Role", roles_for_hosp, format_func=lambda x: ROLE_LABEL.get(x,x))
        staff_id = st.text_input("Staff ID e.g RSUTH-GD01 / RSUTH-REC01 / RSUTH-LAB01")
        staff_pass = st.text_input("Password", type="password", key="staff_pw")
        license_input = ""
        if role_choice in ["general_doctor","dentist"]:
            license_input = st.text_input("Medical License Number e.g MDCN-12345 - Required for Doctors")
        st.info(f"Demo RSUTH: Admin RSUTH-ADMIN/admin123 | Receptionist RSUTH-REC01/recep123 | General RSUTH-GD01/doc123 + MDCN-12345 | Dentist RSUTH-DEN01/doc123 + MDCN-22222 | Lab RSUTH-LAB01/lab123 | Radiographer RSUTH-RAD01/rad123 | Pharmacy RSUTH-PHA01/pha123")
        if st.button("Login as Hospital Staff"):
            s = STAFF.get(staff_id)
            if not s: st.error("Staff ID not found. Contact Admin."); st.stop()
            if s["hospital"]!=hosp: st.error(f"This Staff ID belongs to {s['hospital']}, not {hosp}."); st.stop()
            if s["role"]!=role_choice: st.error(f"This Staff ID is {ROLE_LABEL[s['role']]}, not {ROLE_LABEL[role_choice]}. Choose correct department."); st.stop()
            if s["pass"]!=staff_pass: st.error("Wrong password"); st.stop()
            if role_choice in ["general_doctor","dentist"]:
                if s.get("license","").strip().upper()!=license_input.strip().upper():
                    st.error("❌ License does not match this Doctor ID. Access Denied. Contact Admin."); st.stop()
            st.session_state.update(role=s["role"], user=s["name"], hospital=hosp, staff_id=staff_id); st.rerun()
    with tab3:
        dcode=st.text_input("Driver Code e.g DRV-BMH-01"); dhosp=st.selectbox("Your Hospital", list(HOSPITALS.keys()), key="dhosp")
        if st.button("Login as Driver"):
            if dcode in DRIVERS and DRIVERS[dcode]==dhosp: st.session_state.update(role="driver", hospital=dhosp, user=dcode); st.rerun()
            else: st.error("Wrong driver code / hospital")
    st.stop()

if st.button("Logout"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()

# ============ VICTIM ============
if st.session_state["role"]=="victim":
    st.success(f"Welcome {st.session_state['user']} | Your ID: **{st.session_state['serial']}** | Keep this ID")
    if not st.session_state["chosen_hosp"]:
        st.subheader("Step 2 - 📍 Find Nearby Hospital FIRST")
        col1,col2=st.columns(2)
        with col1: my_lat=st.number_input("Your GPS Latitude", value=4.8156, format="%.4f")
        with col2: my_lon=st.number_input("Your GPS Longitude", value=7.0498, format="%.4f")
        area=st.text_input("If GPS blocked, type your area: Diobu / Mile 1 / Choba / Borikiri / GRA", placeholder="e.g Diobu, Mile 1")
        if st.button("📍 Share My GPS"):
            st.success(f"GPS Saved: {my_lat}, {my_lon}"); st.session_state["gps"]=f"{my_lat},{my_lon}"
        ranked=[]
        for code, h in HOSPITALS.items():
            d=haversine(my_lat, my_lon, h["lat"], h["lon"]); ranked.append((d, code, h))
        ranked.sort()
        st.write("### Nearby Hospitals - Closest First")
        for d, code, h in ranked:
            mins=int(d*3.5)
            c1,c2=st.columns([3,1])
            with c1: st.write(f"**{h['name']}** - {d} km - ~{mins} mins - 📞 {h['phone']}")
            with c2:
                if st.button(f"Choose {code}", key=f"ch_{code}"):
                    st.session_state["chosen_hosp"]=code; st.session_state["step"]="triage"; st.rerun()
        st.stop()
    hosp = st.session_state["chosen_hosp"]
    st.info(f"Chosen Hospital: **{HOSPITALS[hosp]['name']}**")
    if st.button("Change Hospital"): st.session_state["chosen_hosp"]=None; st.rerun()
    td=st.session_state["triage_data"]
    st.subheader(f"Step 3 - AI Nurse Triage for {hosp}")
    if "walk" not in td:
        td["walk"]=st.radio("Q1: Can you walk?", ["Yes","No"], key="q1")
        if st.button("Next"): st.session_state["triage_data"]=td; st.rerun()
    elif "bleeding" not in td:
        td["bleeding"]=st.radio("Q2: Are you bleeding?", ["No","Small","Heavy"], key="q2")
        if st.button("Next"):
            if td["walk"]=="No" and td["bleeding"]=="Heavy": st.session_state["fast_jump"]=True; st.warning("⚠️ CRITICAL! Ambulance NOW.")
            st.session_state["triage_data"]=td; st.rerun()
    elif st.session_state.get("fast_jump") and "address" not in td:
        st.error("🚨 FAST JUMP ACTIVE - Ambulance Starting Now")
        td["address"]=st.text_input("Drop address + phone together (e.g Diobu, Mile 1 - 0803-123-4567)")
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
        td["address"]=st.text_input("Drop address + phone together (e.g Diobu, Mile 1 - 0803-123-4567)")
        if st.button("Submit - Book Ticket / Send Ambulance"):
            td["triage"]=tri; td["gps"]=st.session_state.get("gps","")
            add_patient({"serial":st.session_state["serial"],"name":st.session_state["user"],"phone":td["address"],"hospital":hosp,"triage":tri,"walk":td["walk"],"bleeding":td["bleeding"],"breathe":td["breathe"],"awake":td["awake"],"address":td["address"],"gps":td["gps"]})
            st.session_state["triage_data"]=td; st.session_state["step"]="done"; st.rerun()
    else:
        st.success(f"Done! Your case for {hosp} is booked. Triage: {td.get('triage')}. Your ID: {st.session_state['serial']}")
        if st.button("Start New Case"): st.session_state["triage_data"]={}; st.session_state["chosen_hosp"]=None; st.session_state["fast_jump"]=False; st.rerun()
    st.stop()

# ============ ALL HOSPITAL STAFF + DRIVER + ADMIN ============
hosp = st.session_state.get("hospital")
role = st.session_state["role"]
pats = get_patients(hosp) if hosp else []
pending = [p for p in pats if p['triage']=="CRITICAL" and p['accepted']==0]

st.subheader(f"{ROLE_LABEL.get(role,role)} Dashboard - {hosp} - {st.session_state.get('user')} ({st.session_state.get('staff_id','')})")

# Sound for receptionist / driver / general doctor
if role in ["receptionist","driver","general_doctor"]:
    if not st.session_state["sound_on"]:
        if st.button("🔊 Click Here To Enable Emergency Sound"): st.session_state["sound_on"]=True; st.rerun()
    else: st.success("🔊 Emergency Sound Enabled")
    if st.button("🔇 Mute Sound For 1 Minute"): st.session_state["muted_until"]=time.time()+60; st.success("Muted for 1 min.")
is_muted = time.time() < st.session_state["muted_until"]
has_pending = len(pending)>0 and not is_muted
play_beep_if_needed(has_pending, st.session_state["sound_on"])

# Search
st.write("### 🔍 Search Patient By PHQ ID - Safe RAG")
q=st.text_input("Enter PHQ-XXXX")
if q and q.startswith("PHQ"):
    st.info(safe_rag(q))

# --- EMERGENCY PINNED - Receptionist + Driver + General Doctor see it ---
if role in ["receptionist","driver","general_doctor","admin"]:
    st.write("### 🚨 EMERGENCY - PINNED AT TOP UNTIL ACCEPT")
    if pending:
        for p in pending:
            st.error(f"🚨 {p['serial']} - {p['name']} - {p['hospital']} - {p['triage']} - Bleeding: {p['bleeding']} - Walk: {p['walk']} - Time: {p['created']}")
            st.write(f"**📍 GPS:** https://www.google.com/maps?q={p['gps']}")
            st.write(f"**📍 Address:** {p['address']}")
            st.write(f"**📞 Phone:** {p['phone']}")
            c1,c2,c3=st.columns(3)
            with c1:
                if st.button(f"🚑 ACCEPT & SEND AMBULANCE - {p['serial']}", key=f"acc_{p['id']}"): accept_patient(p['id']); st.success("Accepted! Ambulance moving."); st.rerun()
            with c2:
                if st.button(f"📞 Call Victim {p['serial']}", key=f"call_{p['id']}"): st.info(f"Calling {p['phone']}")
            with c3:
                if st.button(f"✅ Picked Up {p['serial']}", key=f"pick_{p['id']}"): update_status(p['id'],"Picked Up"); st.rerun()
    else: st.success("No pending ambulance emergency.")

# --- RECEPTIONIST: Assign to General Doctor ---
if role=="receptionist":
    st.write("---")
    st.write("### 🧑‍💼 Receptionist - Assign Patient to General Doctor")
    st.caption("You do NOT treat. You register and assign.")
    for p in pats:
        st.write(f"{p['serial']} - {p['name']} - {p['triage']} - Status: {p['status']} - Assigned: {p['assigned_to'] or 'Not yet'}")
        if not p['assigned_to']:
            if st.button(f"➡️ Assign to General Doctor - {p['serial']}", key=f"as_{p['id']}"):
                # Assign to first general doctor of this hospital
                gd = [v["name"] for v in STAFF.values() if v["hospital"]==hosp and v["role"]=="general_doctor"]
                assign_patient(p['id'], gd[0] if gd else "General Doctor"); st.success(f"Assigned to {gd[0] if gd else 'General Doctor'}"); st.rerun()

# --- GENERAL DOCTOR: Consultation Boss + Internal Referral + External Chat ---
if role=="general_doctor":
    st.write("---")
    st.write("### 🩺 General Doctor - CONSULTATION IN CHARGE")
    st.caption("You are the boss of consultation. You examine, you decide, you refer. Admin / Receptionist cannot consult.")
    st.write("#### My Patients - Assigned To Me")
    my_pats = [p for p in pats if p['assigned_to']==st.session_state.get('user') or p['assigned_to']=="General Doctor" or not p['assigned_to']]
    for p in my_pats:
        st.write(f"**{p['serial']} - {p['name']} - {p['triage']} - {p['status']}**")
        # Internal Referral Buttons with SPECIFY
        st.write("**Refer Inside Hospital - Click + Specify What To Do:**")
        # Choose department to refer to
        dept = st.selectbox(f"Choose Department to Refer {p['serial']}", ["-- Choose --","lab","radiographer","dentist","pharmacist"], key=f"dept_{p['id']}")
        test_type = ""
        note = ""
        if dept=="lab":
            test_type = st.selectbox(f"What Lab Test for {p['serial']}?", ["Blood Test","Urine Test","Malaria Test","Pregnancy Test","Blood Sugar","Other"], key=f"lab_{p['id']}")
            note = st.text_input(f"Lab Note for {p['serial']}", key=f"labn_{p['id']}", placeholder="e.g Check blood level")
        elif dept=="radiographer":
            test_type = st.selectbox(f"What Should Radiographer Scan for {p['serial']}?", ["Chest X-ray","Bone / Fracture - Leg","Bone / Fracture - Arm","Skull / Head Scan","Back / Spine","Stomach / Abdomen","Other"], key=f"rad_{p['id']}")
            note = st.text_input(f"Radiographer Note for {p['serial']}", key=f"radn_{p['id']}", placeholder="e.g Suspect broken leg, patient fell")
        elif dept=="dentist":
            test_type = st.selectbox(f"What Dentist Should Do for {p['serial']}?", ["Tooth Pain / Check","Tooth Removal","Gum Bleeding","Mouth Injury","Other"], key=f"den_{p['id']}")
            note = st.text_input(f"Dentist Note for {p['serial']}", key=f"denn_{p['id']}", placeholder="e.g Tooth broken after fall")
        elif dept=="pharmacist":
            st.info("Pharmacy: You may NOT know drug name. Just tell Pharmacist WHAT the drug is FOR. Pharmacist will pick correct drug.")
            know = st.radio(f"Do you know drug name for {p['serial']}?", ["No, I don't know - Tell what it is for","Yes, I know it"], key=f"phk_{p['id']}")
            if know.startswith("No"):
                test_type = st.selectbox(f"What does patient need drug FOR? {p['serial']}", ["Pain Relief / Pain Killer","For Infection / Antibiotic","For Fever / Malaria","For Cough / Cold","For Wound / Injury","For Blood Pressure","For Diabetes / Sugar","Other"], key=f"pha_{p['id']}")
                note = st.text_input(f"Pharmacy Note for {p['serial']}", key=f"phan_{p['id']}", placeholder="e.g Severe leg pain after fall, needs strong pain relief")
            else:
                test_type = "Drug Name Known: " + st.text_input(f"Type Drug Name for {p['serial']}", key=f"phad_{p['id']}")
                note = st.text_input(f"Pharmacy Note for {p['serial']}", key=f"phan2_{p['id']}")
        if dept!="-- Choose --":
            if st.button(f"✅ SEND TO {dept.upper()} - {p['serial']}", key=f"send_{p['id']}"):
                c=conn(); cur=c.cursor(); cur.execute("INSERT INTO internal_referrals (patient_serial,patient_name,hospital,from_doctor,to_dept,test_type,note,status,created) VALUES (?,?,?,?,?,?,?,?,?)",(p['serial'],p['name'],hosp,st.session_state.get('user'),dept,test_type,note,"Pending",datetime.datetime.now().strftime("%d %b %Y %I:%M %p"))); c.commit(); c.close()
                st.success(f"Sent to {dept} - {test_type}. {dept.capitalize()} will see it now.")
                st.rerun()
        if st.button(f"✅ Mark Treated / Discharged - {p['serial']}", key=f"tr_{p['id']}"): update_status(p['id'],"Treated / Discharged"); st.rerun()

    # Internal referrals sent - show results coming back
    st.write("#### 📥 Results Coming Back From Departments")
    c=conn(); c.row_factory=sqlite3.Row; cur=c.cursor(); cur.execute("SELECT * FROM internal_referrals WHERE hospital=? ORDER BY id DESC",(hosp,)); irefs=[dict(r) for r in cur.fetchall()]; c.close()
    for r in irefs:
        st.write(f"{r['patient_serial']} - {r['patient_name']} → {r['to_dept'].upper()} | Test: {r['test_type']} | Note: {r['note']} | Status: {r['status']} | Result: {r['result'] or 'Waiting'}")

    # EXTERNAL: Chat + Transfer to Other Hospital
    st.write("---")
    st.write("### 🏥 External Referral + Chat With Other Hospital - Need Help?")
    st.caption("Chat with another hospital doctor when case is too big, then transfer.")
    to_hosp_chat = st.selectbox("Chat With Hospital", [h for h in HOSPITALS.keys() if h!=hosp], key="chat_to")
    chat_msg = st.text_input("Your Message to Other Hospital Doctor", placeholder="e.g Hello, I have severe head injury patient, what should I do before transfer?")
    if st.button("💬 Send Chat"):
        c=conn(); cur=c.cursor(); cur.execute("INSERT INTO chats (from_hosp,from_name,to_hosp,msg,created) VALUES (?,?,?,?,?)",(hosp,st.session_state.get('user'),to_hosp_chat,chat_msg,datetime.datetime.now().strftime("%d %b %Y %I:%M %p"))); c.commit(); c.close(); st.success(f"Chat sent to {to_hosp_chat}"); st.rerun()
    c=conn(); c.row_factory=sqlite3.Row; cur=c.cursor(); cur.execute("SELECT * FROM chats WHERE to_hosp=? OR from_hosp=? ORDER BY id DESC LIMIT 20",(hosp,hosp)); chats=[dict(r) for r in cur.fetchall()]; c.close()
    for ch in chats:
        st.write(f"💬 {ch['from_hosp']} ({ch['from_name']}) → {ch['to_hosp']}: {ch['msg']} | {ch['created']}")
        if ch['to_hosp']==hosp:
            reply = st.text_input(f"Reply to {ch['from_hosp']}", key=f"rep_{ch['id']}")
            if st.button(f"Reply", key=f"repb_{ch['id']}"):
                c=conn(); cur=c.cursor(); cur.execute("INSERT INTO chats (from_hosp,from_name,to_hosp,msg,created) VALUES (?,?,?,?,?)",(hosp,st.session_state.get('user'),ch['from_hosp'],reply,datetime.datetime.now().strftime("%d %b %Y %I:%M %p"))); c.commit(); c.close(); st.rerun()

    st.write("#### 🚑 Transfer Patient To Another Hospital")
    serial_ref=st.text_input("Patient PHQ ID to Transfer")
    to_hosp=st.selectbox("Transfer To Hospital", list(HOSPITALS.keys()), key="trans_to")
    reason=st.selectbox("Why Transfer?", ["No bed","No blood","Need specialist","Need ICU","Need surgery"])
    msg=st.text_area("Message to Other Doctor")
    if st.button("🔁 Send Transfer"):
        c=conn(); cur=c.cursor(); cur.execute("INSERT INTO referrals (serial,from_hosp,to_hosp,reason,msg,status,created) VALUES (?,?,?,?,?,?,?)",(serial_ref,hosp,to_hosp,reason,msg,"Pending",datetime.datetime.now().strftime("%d %b %Y %I:%M %p"))); c.commit(); c.close(); st.success(f"Transfer sent {hosp} -> {to_hosp} for {serial_ref}")
    c=conn(); c.row_factory=sqlite3.Row; cur=c.cursor(); cur.execute("SELECT * FROM referrals ORDER BY id DESC"); refs=[dict(r) for r in cur.fetchall()]; c.close()
    for r in refs:
        if r['from_hosp']==hosp or r['to_hosp']==hosp:
            st.write(f"Transfer: {r['serial']} {r['from_hosp']} -> {r['to_hosp']} | {r['reason']} | {r['msg']} | Status: {r['status']}")
            if r['to_hosp']==hosp:
                if st.button(f"✅ Accept Transfer {r['id']}", key=f"ra_{r['id']}"): c=conn(); cur=c.cursor(); cur.execute("UPDATE referrals SET status='Accepted' WHERE id=?",(r['id'],)); c.commit(); c.close(); st.rerun()
                if st.button(f"❌ Decline {r['id']}", key=f"rd_{r['id']}"): c=conn(); cur=c.cursor(); cur.execute("UPDATE referrals SET status='Declined - Try Another' WHERE id=?",(r['id'],)); c.commit(); c.close(); st.rerun()

# --- DEPARTMENT PORTALS: Dentist / Lab / Radiographer / Pharmacist ---
if role in ["dentist","lab","radiographer","pharmacist"]:
    st.write("---")
    st.write(f"### {ROLE_LABEL[role]} Portal - {hosp} - You See ONLY Your Department Queue")
    st.caption("General Doctor sent these to you. Do your job, write result, send back to General Doctor.")
    c=conn(); c.row_factory=sqlite3.Row; cur=c.cursor(); cur.execute("SELECT * FROM internal_referrals WHERE hospital=? AND to_dept=? ORDER BY id DESC",(hosp,role)); my_refs=[dict(r) for r in cur.fetchall()]; c.close()
    if not my_refs: st.info("No patient yet. Waiting for General Doctor to send to you.")
    for r in my_refs:
        st.write(f"**{r['patient_serial']} - {r['patient_name']}**")
        if role=="radiographer":
            st.error(f"🩻 SCAN: {r['test_type']} | Note from General Doctor: {r['note']}")
        elif role=="lab":
            st.warning(f"🔬 TEST: {r['test_type']} | Note: {r['note']}")
        elif role=="dentist":
            st.info(f"🦷 DENTIST WORK: {r['test_type']} | Note: {r['note']}")
        elif role=="pharmacist":
            st.success(f"💊 PHARMACY NEED: {r['test_type']} | Note: {r['note']} - You choose correct drug. Doctor told you what it is FOR.")
            if r['test_type'].startswith("Drug Name Known"):
                st.write("Doctor already gave drug name. Give that drug.")
            else:
                st.write("Doctor does NOT know drug name. Pick correct drug for this need.")
        st.write(f"Status: {r['status']} | Result: {r['result'] or 'Not yet'}")
        result_input = st.text_input(f"Write Result / What You Did for {r['patient_serial']}", key=f"res_{r['id']}", placeholder="e.g X-ray shows broken leg / Lab: Blood level low / Drug given: Paracetamol")
        if st.button(f"✅ Done - Send Result Back to General Doctor - {r['patient_serial']}", key=f"done_{r['id']}"):
            c=conn(); cur=c.cursor(); cur.execute("UPDATE internal_referrals SET status='Done - Result Sent to General Doctor', result=? WHERE id=?",(result_input, r['id'])); c.commit(); c.close(); st.success("Result sent back to General Doctor."); st.rerun()

# --- ADMIN ---
if role=="admin":
    st.write("---")
    st.write(f"### 👑 Admin - {hosp} - Manage Staff Only. You Do NOT Treat Patients.")
    st.write("Staff in this hospital:")
    for sid, s in STAFF.items():
        if s["hospital"]==hosp:
            st.write(f"{sid} - {s['name']} - {ROLE_LABEL[s['role']]} - Pass: {s['pass']} - License: {s.get('license','-')}")
    st.write("All Patients in this Hospital:")
    for p in pats:
        st.write(f"{p['serial']} - {p['name']} - {p['triage']} - {p['status']} - Assigned: {p['assigned_to']}")
        if st.button(f"Mark Treated {p['serial']}", key=f"admtr_{p['id']}"): update_status(p['id'],"Treated"); st.rerun()
    st.caption("To add new staff in real app, Admin fills: Name + Hospital + Role + License (if doctor) + Password. No license = No doctor account.")

# --- All Patients List for Staff ---
if role in ["receptionist","general_doctor","admin","driver"]:
    st.write("---")
    st.write("### All Patients - This Hospital")
    for p in pats:
        st.write(f"{p['serial']} - {p['name']} - {p['triage']} - Status: {p['status']} - Accepted: {'Yes' if p['accepted'] else 'No'}")
