import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

logging.basicConfig(level=logging.INFO)


project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "crm.db"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
db = SQLAlchemy(app)


device = "cpu"
model_name = "model"  
tokenizer = None
model = None

try:
    logging.info(f"Loading tokenizer & model from: {model_name} on device: {device}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.to(device)
    model.eval()
    logging.info("AI Model loaded successfully.")

except Exception as e:
    logging.error(f"FATAL: Could not load AI model: {e}")


class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    status = db.Column(db.String(50), default='New Lead')
    notes = db.Column(db.Text)
    sentiment = db.Column(db.String(10), default='neutral')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Lead {self.name}>'

def analyze_sentiment(text):
    if model is None or tokenizer is None:
        logging.error("Sentiment analysis failed: Model/Tokenizer not loaded.")
        return "neutral"
    if not text or not text.strip():
        return "neutral"
    
    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        prediction_idx = torch.argmax(probabilities, dim=-1).item()
        
        sentiment_map_5_labels = {0: "Very Negative", 1: "Negative", 2: "Neutral", 3: "Positive", 4: "Very Positive"}
        sentiment_5_label = sentiment_map_5_labels.get(prediction_idx, "Neutral")
        
        logging.info(f"Raw prediction (5-label): {sentiment_5_label}")

        if sentiment_5_label in ["Positive", "Very Positive"]:
            return "positive"
        elif sentiment_5_label in ["Negative", "Very Negative"]:
            return "negative"
        else: 
            return "neutral"

    except Exception as e:
        logging.error(f"Sentiment analysis runtime error: {e}")
        return "neutral"


@app.route('/')
def index():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template('index.html', leads=leads)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))
        
    file = request.files['file']
    
    if file.filename == '':
        return redirect(url_for('index'))
        
    if file:
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith('.xlsx'):
                df = pd.read_excel(file)
            else:
                return redirect(url_for('index'))
            
            for _, row in df.iterrows():
                notes_text = "" if pd.isna(row.get('notes')) else str(row.get('notes'))
                name_text = "" if pd.isna(row.get('name')) else str(row.get('name'))
                
                if not name_text:
                    continue
                    
                email_text = "" if pd.isna(row.get('email')) else str(row.get('email'))
                phone_text = "" if pd.isna(row.get('phone')) else str(row.get('phone'))
                status_text = "New Lead" if pd.isna(row.get('status')) else str(row.get('status'))

                sentiment = analyze_sentiment(notes_text)
                
                new_lead = Lead(
                    name=name_text,
                    email=email_text,
                    phone=phone_text,
                    status=status_text,
                    notes=notes_text,
                    sentiment=sentiment
                )
                db.session.add(new_lead)
            
            db.session.commit()
            logging.info(f"Successfully imported {len(df)} rows.")

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error importing file: {e}")

    return redirect(url_for('index'))

@app.route('/lead/add', methods=['POST'])
def add_lead():
    data = request.form
    notes = data.get('notes')
    sentiment = analyze_sentiment(notes)
    
    new_lead = Lead(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        status=data.get('status'),
        notes=notes,
        sentiment=sentiment
    )
    db.session.add(new_lead)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/lead/edit/<int:id>', methods=['POST'])
def edit_lead(id):
    lead = Lead.query.get_or_404(id)
    data = request.form
    notes = data.get('notes')
    
    if lead.notes != notes:
        lead.sentiment = analyze_sentiment(notes)
    
    lead.name = data.get('name')
    lead.email = data.get('email')
    lead.phone = data.get('phone')
    lead.status = data.get('status')
    lead.notes = notes
    
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/lead/delete/<int:id>')
def delete_lead(id):
    lead = Lead.query.get_or_404(id)
    db.session.delete(lead)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/api/lead/<int:id>')
def get_lead_data(id):
    lead = Lead.query.get_or_404(id)
    return jsonify({
        'id': lead.id,
        'name': lead.name,
        'email': lead.email,
        'phone': lead.phone,
        'status': lead.status,
        'notes': lead.notes
    })

@app.route('/api/sentiment-stats')
def sentiment_stats():
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    query = db.session.query(Lead.sentiment, func.count(Lead.sentiment))
    
    if start_str and end_str:
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_str + " 23:59:59", '%Y-%m-%d %H:%M:%S')
            query = query.filter(Lead.created_at.between(start_date, end_date))
        except ValueError:
            return jsonify({"error": "Incorrect date format. Use YYYY-MM-DD"}), 400
            
    stats = query.group_by(Lead.sentiment).all()
    
    data = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    for sentiment, count in stats:
        if sentiment in data:
            data[sentiment] = count
            
    return jsonify(data)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)