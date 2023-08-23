from wtforms.fields  import SelectField
from wtforms.widgets import Select, html_params
from markupsafe import Markup



#questi due metodi servono per creare un select custom con un default non selezionabile, necessario perchè Flask-wtforms non permette questa funzionalità
class AttribSelect(Select):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True
        html = ['<select %s>' % html_params(name=field.name, **kwargs)]
        for val, label, selected, html_attribs in field.iter_choices():
            html.append(self.render_option(val, label, selected, **html_attribs))
        html.append('</select>')
        return Markup(''.join(html))

class AttribSelectField(SelectField):
    widget = AttribSelect()

    def iter_choices(self):
        for value, label, render_args in self.choices:
            yield (value, label, self.coerce(value) == self.data, render_args)

    def pre_validate(self, form):
         if self.choices:
             for v, _, _ in self.choices:
                 if self.data == v:
                     break
             else:
                 raise ValueError(self.gettext('Is Not a valid choice'))




from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, BooleanField

class ChatForm(FlaskForm):

    userPrompt = TextAreaField("",default="", render_kw={"class": "textarea", "placeholder": "Inserisci un prompt...."})

    modeSelect = AttribSelectField("", choices=[(-1, 'Scegli una modalità', dict(disabled='disabled')),(0, "Chat generica",dict()), (1, "Esperto sicurezza",dict()), (2, "Generatore slide",dict()), (3, "Traduttore",dict())], coerce=int, default=-1, render_kw={"class": "select"})

    submit = SubmitField("Invio", render_kw={"class": "button", "id" : "send"})

    clearButton = SubmitField("Nuova chat", render_kw={"class": "button"})

    backButton = SubmitField("Back", render_kw={"class": "button"})

    logOutButton = SubmitField("Log Out", render_kw={"class": "logOutButton"})

class ImageForm(FlaskForm):
    
    imagesURLsLen=0

    imagesURLs= []

    userPrompt = TextAreaField("",default="", render_kw={"class": "textarea", "placeholder": "Inserisci un prompt...."})

    numberSelect = AttribSelectField("", choices=[(-1, 'Scegli una quantità', dict(disabled='disabled')),(1, "1",dict()), (2, "2",dict()), (3, "3",dict()), (4, "4",dict()), (5, "5",dict()), (6, "6",dict()), (7, "7",dict()), (8, "8",dict()), (9, "9",dict()), (10, "10",dict())], coerce=int, default=-1, render_kw={"class": "select"})

    qualitySelect = AttribSelectField("", choices=[(-1, 'Scegli la qualità', dict(disabled='disabled')),(0, "Bassa (256x256)",dict()), (1, "Media (512x512)",dict()), (2, "Alta (1024x1024)",dict())], coerce=int, default=-1, render_kw={"class": "select"})

    promptAssist = BooleanField("",default="checked")

    submit = SubmitField("Invio", render_kw={"class": "button", "id" : "send"})

    backButton = SubmitField("Back", render_kw={"class": "button"})

    logOutButton = SubmitField("Log Out", render_kw={"class": "logOutButton"})

class DeleteForm(FlaskForm):
    
    submit = SubmitField("CANCELLAMI", render_kw={"class": "deleteButton"})

    backButton = SubmitField("Back", render_kw={"class": "button"})

class LoginForm(FlaskForm):
    
    username = StringField("", render_kw={"class":"inputField", "placeholder": "Inserisci il tuo username..."})

    password = StringField("", render_kw={"class":"inputField", "placeholder": "Inserisci la tua password...", "type": "password"})

    passCheck = BooleanField("", render_kw={"onClick" : "showPassword()"})

    submit = SubmitField("Log In", render_kw={"class": "button"})

class SubscribeForm(FlaskForm):
    
    username = StringField("", render_kw={"class":"inputField", "placeholder": "Inserisci l'username..."})

    password = StringField("", render_kw={"class":"inputField", "placeholder": "Inserisci la password...", "type": "password"})
    
    confirmPassword = StringField("", render_kw={"class":"inputField", "placeholder": "Conferma la password...", "type": "password"})

    passCheck = BooleanField("", render_kw={"onClick" : "showPassword()"})

    submit = SubmitField("Iscriviti", render_kw={"class": "button"})

class ChatHistory():
    messages=[]
    messagesLen=0
    username=""

    def __init__(self, messages, username):
        self.messages=messages
        self.messagesLen=len(messages)
        self.username=username
   


