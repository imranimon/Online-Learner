from flask import Flask
from flask import render_template, redirect, url_for, session, request
from flask_db2 import DB2
from flask import jsonify
import process

app = Flask(__name__,template_folder='templates')
app.secret_key = "vbdgektiksgfnkeia"

app.config['DB2_DATABASE'] = 
app.config['DB2_HOSTNAME'] = 
app.config['DB2_PORT'] = 
app.config['DB2_PROTOCOL'] = 
app.config['DB2_USER'] = 
app.config['DB2_PASSWORD'] = 

db = DB2(app)
app.debug=True

@app.route('/')
def index():
    cur = db.connection.cursor()

    cur.execute('select kurs.name,kurs.freiePlaetze,benutzer.name,kid from kurs join benutzer on kurs.ersteller=benutzer.bnummer where freiePlaetze>0')
    allcourses=cur.fetchall()
    allcourses_info = process.process_list(allcourses)

    cur.close()
    del cur
    return render_template('index.html',projectinfo=allcourses_info)

@app.route('/signup', methods=["GET", "POST"])
def signup():
    cur = db.connection.cursor()
    message=''
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        cur.execute("select * from benutzer where email=?", (email,))
        result=cur.fetchall()

        if result:
            message = 'You are already registered to our site'
        else:
            cur.execute("insert into benutzer (email, name) values (?,?)", (email, username,))
            return redirect(url_for("login"))
    cur.close()
    del cur
    return render_template('signup.html',message=message)

@app.route('/login', methods=["GET", "POST"])
def login():
    cur = db.connection.cursor()
    message = "Welcome to online learner"
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        if email is not None and username is not None:
            #cur.execute("select email,name,bnummer from benutzer where email= ('" + email + "') and name=('" + username + "')")
            cur.execute("select email,name,bnummer from benutzer where email= ? and name= ?", (email, username))
            result = cur.fetchone()
            loggedinUser=[]
            if result is not None:
                for item in result:
                    loggedinUser.append(item)
            if result:
                session["ses_user"] = loggedinUser
                session['logged_in'] = True
                return redirect(url_for("userdetails"))
            else:
                session['logged_in'] = False
                message="Please input valid information to LOGIN"
    cur.close()
    del cur
    return render_template('login.html',message=message)

@app.route('/logout')
def logout():
    session.pop("ses_user", None)
    return redirect(url_for("login"))

@app.route('/userdetails')
def userdetails():
    if "ses_user" in session:
        userid=session["ses_user"][2]
        cur = db.connection.cursor()

        #cur.execute('select kurs.name,kurs.freiePlaetze,benutzer.name,kurs.kid from kurs join benutzer on kurs.ersteller=benutzer.bnummer join einschreiben on kurs.kid=einschreiben.kid where freiePlaetze >0 and einschreiben.bnummer=%s', (userid,))
        cur.execute('select kurs.name,kurs.freiePlaetze,benutzer.name,kurs.kid from kurs join benutzer on kurs.ersteller=benutzer.bnummer join einschreiben on kurs.kid=einschreiben.kid where freiePlaetze >0 and einschreiben.bnummer=?',(userid,))
        enrolled_courses = cur.fetchall()
        my_enrolled_courses = process.process_list(enrolled_courses)

        cur.execute('select kurs.name,kurs.freiePlaetze,benutzer.name,kurs.kid from kurs join benutzer on kurs.ersteller=benutzer.bnummer where freiePlaetze >0')
        result1 = cur.fetchall()
        allcourses =process.process_list(result1)

        availabe_course = [x for x in allcourses if x not in my_enrolled_courses]

        cur.close()
        del cur
        return render_template('userdetails.html',availavle_course=availabe_course,my_enrolled_courses=my_enrolled_courses)
    else:
        return redirect(url_for("login"))

@app.route('/createcourse',methods=["GET", "POST"])
def createcourse():
    if "ses_user" in session:
        userid = session["ses_user"][2]
        cur = db.connection.cursor()
        message = False
        info=[]
        if request.method == "POST":
            course_name = request.form["course_name"]
            key = request.form["key"]
            available_places = request.form["available_places"]
            course_description = request.form["course_description"]

            if 0<int(len(course_name))<51 and 0<int(available_places)<101 and course_description is not None:
                if key:
                    cur.execute("insert into kurs (name,beschreibungstext,einschreibeschluessel,freiePlaetze,ersteller) values (?,?,?,?,?)", (course_name, course_description, key, available_places,userid,))
                    #cur.execute("insert into kurs (name,beschreibungstext,einschreibeschluessel,freiePlaetze,ersteller) values ('" + course_name + "','" + course_description + "','" + key + "','" + available_places + "',%s)" %(userid))
                else:
                    cur.execute("insert into kurs (name,beschreibungstext,freiePlaetze,ersteller) values (?,?,?,?)", (course_name, course_description, available_places,userid,))
                    #cur.execute("insert into kurs (name,beschreibungstext,freiePlaetze,ersteller) values ('" + course_name + "','" + course_description + "','" + available_places + "',%s)" % (userid))
                return redirect(url_for("userdetails"))
            else:
                message=True
                info=["Your input is wrong.Please follow the instructions"," 1.Length of course name can't be empty and not greater than 50"," 2.Availave places have to be in between 1 and 100"," 3.Course Description can't be empty"]
        cur.close()
        del cur
        return render_template('newcourse..html',message=message,info=info)
    else:
        return redirect(url_for("login"))

@app.route('/coursedetails/<cid>')
def coursedetails(cid):
    if "ses_user" in session:
        userid = session["ses_user"][2]
        cur = db.connection.cursor()
        cur.execute('select * from einschreiben where kid=? and bnummer=?', (cid,userid))
        enrolled=cur.fetchall()

        course_creator=False
        cur.execute("select ersteller from kurs where kid=?", (cid,))
        creator=cur.fetchone()
        if creator[0]==userid:
            course_creator=True

        cur.execute('select kurs.name,kurs.freiePlaetze,benutzer.name,kid,kurs.beschreibungstext from kurs join benutzer on kurs.ersteller=benutzer.bnummer where kid=?', (cid,))
        enrolled_course=cur.fetchall()
        enrolled_course_result=process.process_list(enrolled_course)

        cur.execute('select name,anummer from aufgabe where kid=? order by anummer ASC',(cid,))
        aufgabe_info=cur.fetchall()
        aufgabe_info_result=process.process_list(aufgabe_info)

        #cur.execute('select aufgabe.name,einreichen.abgabetext,einreichen.bnummer,einreichen.eid,aufgabe.anummer from aufgabe left join einreichen on aufgabe.anummer=einreichen.anummer where aufgabe.kid=? order by aufgabe.anummer ASC', (cid,))
        cur.execute('select abgabetext,eid,anummer from einreichen where kid=? and bnummer=?', (cid,userid))
        submission_info=cur.fetchall()
        submission_info_result=process.process_list(submission_info)
        print(submission_info_result)

        cur.execute('select avg(note) as avg_note,eid from bewerten group by eid')
        bewerten_info=cur.fetchall()
        bewerten_info_result=process.process_list(bewerten_info)

        cur.execute('select kurs.name,kurs.freiePlaetze,benutzer.name,kid,kurs.beschreibungstext from kurs join benutzer on kurs.ersteller=benutzer.bnummer where kid=?', (cid,))
        unenrolled_course = cur.fetchall()
        unenrolled_course_result = process.process_list(unenrolled_course)

        cur.close()
        del cur
        return render_template('coursedetails.html',enrolled=enrolled,enrolled_course_result=enrolled_course_result,unenrolled_course_result=unenrolled_course_result,aufgabe_info_result=aufgabe_info_result, submission_info_result=submission_info_result, bewerten_info_result=bewerten_info_result,course_creator=course_creator, cid=cid,userid=userid)

    else:
        return redirect(url_for("login"))

@app.route('/enroll/<cid>',methods=["GET", "POST"])
def enroll(cid):
    if "ses_user" in session:
        userid = session["ses_user"][2]
        cur = db.connection.cursor()
        message = ''
        cur.execute('select name from kurs where kid=?', (cid,))
        cname = cur.fetchone()
        hasKey='Yes'
        cur.execute('select einschreibeschluessel from kurs where kid=?', (cid,))
        reg_key = cur.fetchone()
        if reg_key[0] is None:
            hasKey = 'NO'
        if request.method == "POST":
            try:
                key = request.form["key"]
            except:
                key=None
            cur.execute('select * from einschreiben where kid=? and bnummer=?', (cid, userid))
            enrolled = cur.fetchall()
            cur.execute("select freiePlaetze from kurs where kid=?", (cid,))
            freeplace=cur.fetchone()

            if int(freeplace[0])>0:
                if enrolled:
                    message='You are already enrolled in this course'
                else:
                    if reg_key[0]==key:
                        cur.execute('insert into einschreiben(bnummer,kid) values (?,?)', (userid,cid))
                        cur.execute('update kurs set freiePlaetze=freiePlaetze-1 where kid=?', (cid,))
                        return redirect(url_for("coursedetails",cid=cid))
                    elif reg_key[0]!=key:
                        message='Registration key is not correct'
                    elif reg_key[0] is None:
                        cur.execute('insert into einschreiben(bnummer,kid) values (?,?)', (userid, cid))
                        cur.execute('update kurs set freiePlaetze=freiePlaetze-1 where kid=?', (cid,))
                        return redirect(url_for("coursedetails", cid=cid))
            else:

                message='Course is full.No new enrollment possible.'
        cur.close()
        del cur
        return render_template('enroll.html',message=message,cname=cname[0],has_key=hasKey)
    else:
        return redirect(url_for("login"))


@app.route('/delete/<cid>')
def delete(cid):
    if "ses_user" in session:
        userid = session["ses_user"][2]
        cur = db.connection.cursor()
        message=''
        cur.execute("select ersteller from kurs where kid=?", (cid,))
        creator = cur.fetchone()
        if creator[0] == userid:
            cur.execute("delete from kurs where kid=?", (cid,))
            return redirect(url_for("userdetails"))
        else:
            message="You can't delte this course !!"
        cur.close()
        del cur
        return render_template('message.html',message=message)
    else:
        return redirect(url_for("login"))

@app.route('/createtask/<cid>',methods=["GET", "POST"]) #done
def createtask(cid):
    if "ses_user" in session:
        userid = session["ses_user"][2]
        cur = db.connection.cursor()
        message = False
        info = []
        cur.execute("select ersteller from kurs where kid=?", (cid,))
        creator = cur.fetchone()

        if request.method == "POST":
            task_name = request.form["task_name"]
            description = request.form["description"]
            if creator[0] == userid:
                if 0 < int(len(task_name)) < 51 and 0 < int(len(description)):
                    print(cid,task_name,description)
                    cur.execute(f"insert into aufgabe(kid,name,beschreibung) values (?,?,?)", (cid, task_name, description))
                    return redirect(url_for("coursedetails", cid=cid))
                else:
                    message=True
                    info=["Your input is wrong","1.Task name can't be empty or greater than 50","2.Task description can't be empty"]
            else:
                message = True
                info = ["You can't create any task for this course"]
        cur.close()
        del cur
        return render_template('createtask.html',message=message,info=info)
    else:
        return redirect(url_for("login"))

@app.route('/submission/<cid>/<tid>',methods=["GET", "POST"])
def submission(cid,tid):
    if "ses_user" in session:
        userid = session["ses_user"][2]
        cur = db.connection.cursor()
        message = False
        info = []
        cur.execute("select * from einreichen where bnummer=? and kid=? and anummer=?", (userid,cid,tid))
        submission_exists=cur.fetchall()

        cur.execute('select name from kurs where kid=?', (cid,))
        cname = cur.fetchone()

        cur.execute("select name,beschreibung from aufgabe where anummer=?",(tid,))
        aufgabe_info=cur.fetchone()

        if submission_exists:
            message=True
            info=["You have already submitted your answer for this task","So you can't submit again"]
        else:
            if request.method == "POST":
                answer = request.form["answer"]
                cur.execute(f"INSERT INTO einreichen (bnummer, kid, anummer, abgabetext)  VALUES (?,?,?,?)", (userid,cid,tid, answer))
                return redirect(url_for("coursedetails",cid=cid))
        cur.close()
        del cur
        return render_template('submussion.html',message=message,info=info,cname=cname[0],aufgabe_info=aufgabe_info)
    else:
        return redirect(url_for("login"))


@app.route('/allcourses')
def allcourses():
    if "ses_user" in session:
        userid = session["ses_user"][2]
        cur = db.connection.cursor()

        cur.execute('select kurs.name,kurs.freiePlaetze,benutzer.name,kid from kurs join benutzer on kurs.ersteller=benutzer.bnummer where freiePlaetze>0')
        allcourses = cur.fetchall()
        allcourses_info = process.process_list(allcourses)

        cur.close()
        del cur
        return render_template('allcourses.html', projectinfo=allcourses_info)
    else:
        return redirect(url_for("login"))
@app.route('/allsubmission/<cid>/<cname>')
def allsubmission(cid,cname):
    if "ses_user" in session:
        userid = session["ses_user"][2]
        cur = db.connection.cursor()

        cur.execute('select abgabetext,eid,anummer from einreichen where kid=? and bnummer!=?', (cid, userid))
        submission_info = cur.fetchall()
        submission_info_result = process.process_list(submission_info)
        print(submission_info_result)



        cur.close()
        del cur
        return render_template('allsubmission.html', submission_info_result=submission_info_result,cname=cname,userid=userid,cid=cid)
    else:
        return redirect(url_for("login"))

@app.route('/rating/<eid>/<cname>/<submission>',methods=["GET", "POST"])
def rating(eid,cname,submission):
    if "ses_user" in session:
        userid = session["ses_user"][2]
        cur = db.connection.cursor()
        message = False
        info = ""

        cur.execute('select bnummer,eid,note from bewerten where bnummer=? and eid=?', (userid, eid))
        result = cur.fetchall()
        result_yes = process.process_list(result)
        if result_yes:
            message = True
            info = "You have already rated this submission"
        else:
            if request.method == "POST":
                rating = request.form["rating"]
                answer = request.form["answer"]
                if answer:
                    cur.execute(f"insert into bewerten(bnummer,eid,note) values (?,?,?)",(userid,eid,rating))
                    return redirect(url_for("allcourses"))
                else:
                    cur.execute(f"insert into bewerten(bnummer,eid,note,kommentar) values (?,?,?,?)",(userid,eid,rating,answer))
                    return redirect(url_for("allcourses"))

        cur.close()
        del cur
        return render_template('rating.html',cname=cname, submission=submission,message=message,info=info)

    else:
        return redirect(url_for("login"))

if __name__ == '__main__':
    app.run()

