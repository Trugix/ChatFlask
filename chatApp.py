import os
from flask import Flask, render_template, request, flash, redirect, url_for
from elements import ChatForm, ChatHistory, LoginForm, SubscribeForm, ImageForm, DeleteForm
from chatManager import generateOutput, generateImages
from flask_sqlalchemy import SQLAlchemy
import bcrypt

PROMPT_CREATING = 4

basedir = os.path.abspath(os.path.dirname(__file__)) #prende il path della directory di questo file

app = Flask(__name__)
app.secret_key = os.getenv("chatFlaskKey")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db') #path del database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#Creazione tabella users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(64), nullable=False)

#Creazione tabella messaggi
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.ForeignKey("user.id"), nullable=False)
    userMessage = db.Column(db.Text, nullable=False)
    botMessage = db.Column(db.Text, nullable=False)


#handle indirizzo /index/<user>
@app.route('/index/<user>')
def index(user):
    return render_template("index.html", user=user)


#handle indirizzo /chatText/<user>
@app.route('/chatText/<user>', methods = ['GET', 'POST'])
def chatText(user):
    if (not queryUserPassword(user)):       #se l'user non esiste manda il client al login per evitare accessi diretti a chatText da utenti inesistenti
        return redirect(url_for("login"))
    form = ChatForm()
    if request.method == 'POST':        #tutto il codice sotto questo if viene interpretato quando la pagina viene caricata in POST ovvero quando si preme il bottone submit("Invio")
        if form.validate() == False:
            flash('Errore')
        else:
            input = request.form["userPrompt"] 
            if form.clearButton.data==True:     #se il client preme il bottone "Nuova chat", chiamo dropHistory(user)
                dropHistory(user)
            elif form.backButton.data==True:        #se il client preme il bottone "Back" lo rimando all'index
                return redirect(url_for("index", user=user))
            elif form.logOutButton.data==True:        #se il client preme il bottone "Log Out" lo rimando al login
                return redirect(url_for("login"))
            elif input.strip():                             #controllo input non vuoto
                mode = form.modeSelect.data
                if mode==-1:                        #controllo che il client abbia selezionato una modalità
                    flash('Seleziona una modalità')
                else:
                    form.userPrompt.data=""         #svuota il campo prompt
                    history = ChatHistory(buildHistory(user), user)     #prepare lo storico dei messaggi precedenti
                    try:  
                        output = generateOutput(mode, input, history.messages)  #chiamata a GPT
                        insertMessages(user, input, output)     #inserimento dei nuovi messaggi nel database
                    except Exception as exception:
                        flash(str(exception))
            else:
                flash("Inserisci un prompt")
    history = ChatHistory(buildHistory(user), user)     #prepare lo storico dei messaggi
    return render_template('chatText.html', form = form, history = history)     


#handle indirizzo /imageGen/<user>
@app.route('/imageGen/<user>', methods = ['GET', 'POST'])
def imageGen(user):
    if (not queryUserPassword(user)):       #se l'user non esiste manda il client al login per evitare accessi diretti a chatText da utenti inesistenti
        return redirect(url_for("login"))
    form = ImageForm()
    input=""
    improvedPrompt=""
    if request.method == 'POST':        #tutto il codice sotto questo if viene interpretato quando la pagina viene caricata in POST ovvero quando si preme il bottone submit("Invio")
        if form.validate() == False:
            flash('Errore')
        else:
            input = request.form["userPrompt"]      
            if form.backButton.data == True:              #se il client preme il bottone "Back" lo rimando all'index
                return redirect(url_for("index", user=user))
            elif form.logOutButton.data==True:        #se il client preme il bottone "Log Out" lo rimando al login
                return redirect(url_for("login"))
            else: 
                imagesNum = form.numberSelect.data
                quality = form.qualitySelect.data
                if ( imagesNum == -1):                           #controllo che il client abbia selezionato un numero per le immagini
                    flash('Seleziona un numero di immagini')
                elif (quality == -1):                                   #controllo che il client abbia selezionato una qualità per le immagini
                    flash('Seleziona una qualità per le immagini')
                elif input:       
                    form.userPrompt.data=""         #svuota il campo prompt
                    if form.promptAssist.data is True:          #controllo se il client ha selezionato di essere assistito 
                        try:
                            improvedPrompt = generateOutput(PROMPT_CREATING, input, [])     #mando il prompt del client a GPT per migliorarlo
                        except Exception as exception:
                            flash(str(exception))
                    try:
                        form.imagesURLs = generateImages(input, imagesNum, quality)     #mando il prompt a DALL-e
                        form.imagesURLsLen= len(form.imagesURLs)
                    except Exception as exception:
                        flash(str(exception))
                else:
                    flash("Inserisci un prompt")
    return render_template("imageGen.html", form = form, user=user, userPrompt=input, improvedPrompt=improvedPrompt)


#handle indirizzo /tutorial/
@app.route('/tutorial')
def tutorial():
    return render_template("tutorial.html")


#handle indirizzo /login
@app.route('/login', methods = ['GET', 'POST'])
def login():
    logForm = LoginForm()
    if request.method == 'POST':        #tutto il codice sotto questo if viene interpretato quando la pagina viene caricata in POST ovvero quando si preme il bottone submit("Log In")
        username = request.form["username"]
        password = request.form["password"]
        if check(username, password):      #controllo username e password
            return redirect(url_for("index", user=username))
        else:
            flash('Username e/o password errati')
    return render_template("login.html", logForm=logForm)

#handle indirizzo /subscribe
@app.route('/subscribe', methods = ['GET', 'POST'])
def subscribe():
    subscribeForm = SubscribeForm()
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        confirmPassword = request.form["confirmPassword"]
        if(password!=confirmPassword):          #controllo che i due campi coincidano
            flash("Le password non coincidono")
        elif insertUser(username, password):    #provo a inserire <user, password>
            return redirect(url_for("login"))
        else: 
            flash("Username già in uso")
    return render_template("subscribe.html", subscribeForm=subscribeForm)

@app.route('/delete/<user>', methods = ['GET', 'POST'])
def delete(user):
    form = DeleteForm()
    if request.method == 'POST':        #tutto il codice sotto questo if viene interpretato quando la pagina viene caricata in POST ovvero quando si preme il bottone submit("Log In")
        if form.backButton.data == True:              #se il client preme il bottone "Back" lo rimando all'index
            return redirect(url_for("index", user=user))
        else: 
            if dropUser(user):
                return redirect(url_for("login"))
            else:
                flash("Errore nella cancellazione")
    return render_template("delete.html", form=form, user=user)


#Inserisce nuovi utenti nel database, controlla che non ci siano altri utenti con lo stesso username
#Torna True o False a seconda che l'inserimento vada a buon fine o no
def insertUser(inputUsername, inputPassword):
    if queryUserPassword(inputUsername) is False:
        user = User( username=inputUsername, password=bcrypt.hashpw(inputPassword.encode("utf-8"), bcrypt.gensalt()) )
        db.session.add(user)
        db.session.commit()
        return True
    else:
        return False

#Controlla che l'username e password inseriti corrispondano
def check(username, password):
    hashed = queryUserPassword(username)   #prende dal database la password associata all'username inserito
    if(hashed):
        return bcrypt.checkpw(password.encode("utf-8"), hashed)
    else:
        return False

#Cerca nel database una password associata all'username, ritornandola o tornando False nel caso non esista
def queryUserPassword(inputUsername):
    user = User.query.filter_by(username=inputUsername).first()
    if user is None:
        return False 
    else:
        return user.password


#Cerca nel database l'id che corrisponde all'username
def queryUserId(inputUsername):
    user = User.query.filter_by(username=inputUsername).first()
    if user is not None:
        return user.id
    else:
        return False 

#Inserisce nel database i messaggi associandoli all'id dell'user
def insertMessages(user, userMessageIn, botMessageIn):
    userIdIn = queryUserId(user)
    message = Message(userId=userIdIn, userMessage=userMessageIn, botMessage=botMessageIn)
    db.session.add(message)
    db.session.commit()


#Compone lo storico come lista di messaggi scambiati tra user e GPT
def buildHistory(username):
    userIdIn = queryUserId(username)
    messages = Message.query.filter_by(userId=userIdIn).order_by(Message.userId)
    history=[]
    for message in messages:
        history.append(message.userMessage)
        history.append(message.botMessage)
    return history


#Elimina tutti i messaggi associati ad un certo user
def dropHistory(username):
    userIdIn = queryUserId(username)
    history = Message.query.filter_by(userId=userIdIn)
    for instance in history:
        db.session.delete(instance)
    db.session.commit()

def dropUser(inputUsername):
    user = User.query.filter_by(username=inputUsername).first()
    if user is not None:
        dropHistory(inputUsername)
        db.session.delete(user)
        db.session.commit()
        return True
    else:
        return False 

if __name__ == '__main__':
   app.run(debug=True)