from transformers import TFAutoModel, AutoTokenizer
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import tensorflow as tf
from transformers import TFBertForSequenceClassification, BertTokenizer
import pickle
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import json

app = Flask(__name__)
CORS(app)

model_save_path = 'model' 
tokenizer_save_path = 'tokenizer'
label_encoder_save_path = 'label_encoder.pkl' 

model = TFBertForSequenceClassification.from_pretrained(model_save_path)

tokenizer = BertTokenizer.from_pretrained(tokenizer_save_path)

with open(label_encoder_save_path, 'rb') as file:
    label_encoder = pickle.load(file)

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

db_params = config.get('database', {})

def predict_class(sentence, model, tokenizer, label_encoder):
    inputs = tokenizer(sentence, padding=True, truncation=True, max_length=128, return_tensors="tf")

    logits = model(inputs.data).logits

    probabilities = tf.nn.softmax(logits, axis=-1)

    predicted_class_idx = tf.argmax(probabilities, axis=-1).numpy()[0]

    confidence_score = probabilities[0, predicted_class_idx].numpy()

    predicted_class = label_encoder.inverse_transform([predicted_class_idx])[0]
    
    return predicted_class, confidence_score

@app.route('/predict', methods=['POST'])
def predict():
    sentence = request.json.get("sentence")
    if not sentence:
        return jsonify({"error": "No sentence provided"}), 400

    time_keywords = ['today', 'month', 'week']
    time_frame = 'week'
    for keyword in time_keywords:
        if keyword in sentence:
            time_frame = keyword
            sentence = sentence.replace(keyword, '').strip()

    predicted_class, confidence_score = predict_class(sentence, model, tokenizer, label_encoder)
    confidence_score = float(confidence_score)

    if confidence_score >= 0.7 and time_frame:
        predicted_class += f"_{time_frame}"
    elif confidence_score < 0.7:
        predicted_class = 'Ambiguous'

    return jsonify({
        "class": predicted_class,
        "confidence": confidence_score
    })

@app.route('/retrieve_best_machine', methods=['POST'])
def retrieve_best_machine():
    time_frame = request.json.get('time_frame', 'default')  # 'today', 'month', 'year', or default
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        if time_frame == 'today':
            sql_query = """
            SELECT machine, oee_today FROM pac_processed_data 
            ORDER BY oee_today DESC LIMIT 1
            """
        elif time_frame == 'month':
            sql_query = """
            SELECT machine, oee_month FROM pac_processed_data 
            ORDER BY oee_month DESC LIMIT 1
            """
        else:
            sql_query = """
            SELECT machine, oee_week FROM pac_processed_data 
            ORDER BY oee_week DESC LIMIT 1
            """
            
        
        cur.execute(sql_query)
        best_machine = cur.fetchone()
        cur.close()

        if best_machine:
            return jsonify({
                "machine": best_machine[0],
                "oee": float(best_machine[1])
            })
        else:
            return jsonify({"error": "No machines found."}), 404
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error occurred."}), 500
    finally:
        if conn is not None:
            conn.close()

@app.route('/retrieve_worst_machine', methods=['POST'])
def retrieve_worst_machine():
    time_frame = request.json.get('time_frame', 'default')  # 'today', 'month', 'year'
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        if time_frame == 'today':
            sql_query = """
            SELECT machine, oee_today FROM pac_processed_data 
            ORDER BY oee_today ASC LIMIT 1
            """
        elif time_frame == 'month':
            sql_query = """
            SELECT machine, oee_month FROM pac_processed_data 
            ORDER BY oee_month ASC LIMIT 1
            """
        else:
            sql_query = """
            SELECT machine, oee_week FROM pac_processed_data 
            ORDER BY oee_week ASC LIMIT 1
            """
            
        
        cur.execute(sql_query)
        best_machine = cur.fetchone()
        cur.close()

        if best_machine:
            return jsonify({
                "machine": best_machine[0],
                "oee": float(best_machine[1])
            })
        else:
            return jsonify({"error": "No machines found."}), 404
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error occurred."}), 500
    finally:
        if conn is not None:
            conn.close()
 
if __name__ == '__main__':
    app.run(debug=True)